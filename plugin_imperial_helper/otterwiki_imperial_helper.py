#!/usr/bin/env python3
import re, flask
from otterwiki.plugins import hookimpl, plugin_manager

class ImperialHelper:
    feet_and_inches = re.compile(r"([\d\.]+)' ?([\d\.]+)\"")
    simple_units = re.compile(r"([\d\.]+) ?(ft|in|mi|lbs)(?!\w)")

    @hookimpl
    def setup(
        self, app: flask.Flask, db, storage
    ) -> None:
        self.app = app

    @staticmethod
    def convert_feet_and_inches(m: re.Match) -> str:
        inches = float(m.group(1)) * 12 + float(m.group(2))

        return f'<span class="unit-tooltip" title="{inches * 2.54:.1f}cm">{m.group(0)}</span>'
    
    @staticmethod
    def convert_simple_unit(m: re.Match) -> str:
        conversions = {
            "ft": {"factor": 30.48, "to": "cm"},
            "in": {"factor": 2.54, "to": "cm"},
            "mi": {"factor": 1.60934, "to": "km"},
            "lbs": {"factor": 0.453592, "to": "kg"}
        }

        value = float(m.group(1))
        unit = m.group(2)

        if unit in conversions:
            return f'<span class="unit-tooltip" title="{value * conversions[unit]["factor"]:.1f}{conversions[unit]["to"]}">{m.group(0)}</span>'

        return m.group(0) 

    @hookimpl
    def renderer_markdown_preprocess(self, md: str) -> str | None:
        md = self.feet_and_inches.sub(self.convert_feet_and_inches, md)
        md = self.simple_units.sub(self.convert_simple_unit, md)
        return md
    
    @hookimpl
    def renderer_html_postprocess(self, html: str) -> str | None:
        return html + """<style>
            .unit-tooltip {
                text-decoration-style: wavy;
                text-decoration-line: underline;
                text-decoration-color: var(--dm-border-color);
            }
        </style>"""

plugin_manager.register(ImperialHelper())