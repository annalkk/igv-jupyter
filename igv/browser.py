from IPython.display import HTML, display
import json
import random
from .comm import IGVComm


class Browser:

    # Always remember the *self* argument
    def __init__(self, config):
        """Initialize an igv Browser object.  See https://github.com/igvteam/igv.js/wiki/Browser-Configuration-2.0
        for configuration options.

        Arguments:
            config: A dictionary specifying the browser configuration.  This will be converted to JSON and passed
                    to igv.js  "igv.createBrowser(config)" as described in the igv.js documentation.
        """

        id = self._gen_id()
        config["id"] = id
        self.igv_id = id
        self.config = config
        self.comm = IGVComm("igvcomm")
        self.status = "initializing"
        self.locus = None
        self.eventHandlers = {}

        # Add a callback for received messages.
        @self.comm.comm.on_msg
        def _recv(msg):
            data = json.loads(msg['content']['data'])
            print(json.dumps(data))
            if 'status' in data:
                self.status = data['status']
            elif 'locus' in data:
                self.locus = data['locus']
            elif 'event' in data:
                if data['event'] in self.eventHandlers:
                    handler = self.eventHandlers[data['event']]
                    eventData = None
                    if 'data' in data:
                        eventData = data['data']
                    handler(eventData)


    def show(self):
        """
        Create an igv.js "Browser" instance on the front end.
        """
        display(HTML("""<div id="%s" class="igv-js"></div>""" % (self.igv_id)))
        # DON'T check status before showing browser,
        msg = json.dumps({
            "id": self.igv_id,
            "command": "create",
            "options": self.config
        })
        self.comm.send(msg)

    def search(self, locus):
        """
        Go to the specified locus.
        :param locus: String of the form  "chromsosome:start-end", or for supported genomes a gene name.
        """

        return self._send({
            "id": self.igv_id,
            "command": "search",
            "locus": locus
        })

    def zoom_in(self):
        """
        Zoom in by a factor of 2
        """
        return self._send({
            "id": self.igv_id,
            "command": "zoomIn"
        })

    def zoom_out(self):
        """
        Zoom out by a factor of 2
        """
        return self._send({
            "id": self.igv_id,
            "command": "zoomOut"
        })

    def load_track(self, track):
        """
        Load a track.  Corresponds to the igv.js Browser function loadTrack (see https://github.com/igvteam/igv.js/wiki/Browser-Control-2.0#loadtrack).
        :param track: A dictionary specifying track options.  See https://github.com/igvteam/igv.js/wiki/Tracks-2.0.
        """
        return self._send({
            "id": self.igv_id,
            "command": "loadTrack",
            "track": track
        })

    def on(self, eventName, cb):
        """
        Subscribe to an igv.js event.
        :param eventName: Name of the event.  Currently only "locuschange" is supported.
        :param cb: A callback function taking a single argument.  For the locuschange event this argument will contain
                   a dictionary of the form  {chr, start, end}
        """
        self.eventHandlers[eventName] = cb
        return self._send({
            "id": self.igv_id,
            "command": "on",
            "eventName": eventName
        })

    def remove(self):
        """
        Remove the igv.js Browser instance from the front end.  The browser object should be disposed of after calling
        this method.
        """
        return self._send({
            "id": self.igv_id,
            "command": "remove"
        })

    def _send(self, msg):

        if self.status == "ready":
            self.comm.send(json.dumps(msg))
            return "OK"
        else:
            return "IGV Browser not ready"

    def _gen_id(self):
        return 'igv_' + str(random.randint(1, 10000000))