#!/usr/bin/env python3
import re, yaml, flask
from otterwiki.plugins import hookimpl, plugin_manager

class ImageBox:
    boxes = re.compile("```imagebox(.+?)```", flags=re.DOTALL)
    template_str = """
<div class="imagebox" style="float: right; margin-left: 1.5rem;">
    <a href="{{ url | safe}}"><img src="{{ url | safe}}" alt="{{ desc | safe }}"></a>
    
    {{desc | safe}}

</div>
""".replace("    ", "")

    def create_box(self, m: re.Match) -> str:
        try:
            imagebox_data = yaml.safe_load(m.group(1))
        except:
            return "> [!WARNING]\n> Invalid Image Box!\n\n" + m.group(0)

        return flask.render_template_string(self.template_str, url = imagebox_data["url"], desc = imagebox_data["desc"])

    @hookimpl
    def renderer_markdown_preprocess(self, md: str) -> str | None:
        def repl(m: re.Match) -> str:
            return self.create_box(m)

        return self.boxes.sub(repl, md)

    @hookimpl
    def renderer_html_postprocess(self, html: str) -> str | None:
        return html + """<style>
            .imagebox {
                background-color: rgba(0, 0, 0, 0.1);
                padding: 1rem;
                width: min-content;
            }
            .imagebox p {
                margin: 0;
            }
            .imagebox img {
                max-width: 250px;
            }
            @media (width <= 650px) {
                .imagebox {
                    width: 100%;
                }
            }
        </style>"""

plugin_manager.register(ImageBox())