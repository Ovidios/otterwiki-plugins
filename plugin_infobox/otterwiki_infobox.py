#!/usr/bin/env python3
import re, yaml, flask
from otterwiki.plugins import hookimpl, plugin_manager

class InfoBox:
    boxes = re.compile("```infobox(.+?)```", flags=re.DOTALL)
    template_str = """
<table class="infobox" style="float: right; margin-left: 1.5rem;">
    {% if 'i_title' in infobox_data %}
    <thead>
        <tr>
            <th colspan="2" style="text-align: center; border-bottom: none; font-size-adjust: 0.6;">

            {{ infobox_data['i_title'] }}

            </th>
        </tr>
    </thead>
    {% endif %}
    <tbody>
        {% for k, v in infobox_data.items() %}
        <tr>
            {% if k == 'i_image' %}
            <td colspan="2" style="text-align: center;">
                <a href="{{ v['url'] }}"><img src="{{ v['url'] }}" alt="{{ v['desc'] | safe }}"></a>

                {{ v['desc'] | safe }}

            </td>
            {% elif k == 'i_section' %}
            <td class="infobox-section-head" colspan="2" style="text-align: center; font-weight: bold;">

            {{ v | safe }}

            </td>
            {% elif k != 'i_title' %}
            <td>
            
            {{ k | safe }}
            
            </td>
            <td>
            
            {{ v | safe }}
            
            </td>
            {% endif %}
        </tr>
        {% endfor %}
    </tbody>
</table>
""".replace("    ", "")

    def create_box(self, m: re.Match) -> str:
        try:
            infobox_data = yaml.safe_load(m.group(1))
        except:
            return "> [!WARNING]\n> Invalid Infobox!\n\n" + m.group(0)

        return flask.render_template_string(self.template_str, infobox_data = infobox_data)

    @hookimpl
    def renderer_markdown_preprocess(self, md: str) -> str | None:
        def repl(m: re.Match) -> str:
            return self.create_box(m)

        return self.boxes.sub(repl, md)

    @hookimpl
    def renderer_html_postprocess(self, html: str) -> str | None:
        return html + """<style>
            .infobox p {
                margin: 0;
            }
            .infobox img {
                max-width: 300px;
            }
            .infobox tr td:not([colspan='2']):first-of-type {
                font-weight: bold;
            }
            .page .infobox tbody tr td {
                border: none;
            }
            .infobox-section-head {
                background-color: rgba(0, 0, 0, 0.2);
            }
            @media (width <= 650px) {
                .infobox {
                    width: 100%;
                }
            }
        </style>"""

plugin_manager.register(InfoBox())