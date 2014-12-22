import json
import urllib
from Acquisition import aq_inner
from Products.Five import BrowserView


class MegaphoneEmbedWidgetView(BrowserView):

    def _get_embed_js_defaults(self):
        # default values for embed - depends on request params
        context = aq_inner(self.context)
        request = self.request
        defaults = dict(
            uid=context.UID(),
            show_text=1,
            width=300,
            height=500
        )
        for k in defaults:
            v = request.get(k)
            if v:
                if k in ('width', 'height'):
                    try:
                        defaults[k] = int(v)
                    except ValueError:
                        pass
                else:
                    defaults[k] = urllib.quote(v)
        return defaults

    def embed_js(self):
        """
        <script type="text/javascript" src="//server/folder/my-megaphone/embed.js"></script>
        <div id="megaphone-widget-f363b14f0d714c6b83fbd5ba7c37467a"></div>
        """
        context = aq_inner(self.context)
        self.request.response.setHeader('Content-Type', 'application/javascript;charset=utf-8')

        data = dict(
            url=context.absolute_url()
        )
        defaults = self._get_embed_js_defaults()
        data['defaults_js'] = json.dumps(defaults)
        result = """
(function () {
    var Settings = %(defaults_js)s;

    function EncodeQueryData(data) {
       var ret = [];
       for (var d in data)
          ret.push(encodeURIComponent(d) + "=" + encodeURIComponent(data[d]));
       return ret.join("&");
    }

    function show_frame() {
        var frame = document.createElement('iframe');
        frame.src = "%(url)s/embed-megaphone?" + EncodeQueryData(Settings);
        frame.frameborder = "no";
        frame.id = 'megaphone-frame-' + Settings.uid;
        frame.style = {};
        frame.style.width = "100%%";
        frame.style.height = "100%%";
        var wrapper = document.querySelector('#megaphone-widget-' + Settings.uid);
        wrapper.style = {};
        wrapper.style.width = Settings.width;
        wrapper.style.height = Settings.height;
        wrapper.appendChild(frame);
    }

    document.onreadystatechange = function() {
        if (document.readyState === 'complete') {
            // DOM is ready!
            try {
                show_frame();
            } catch(e) {}
        }
    }
}).call(this);
""" % data
        return result
