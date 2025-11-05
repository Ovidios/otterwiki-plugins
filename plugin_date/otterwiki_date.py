#!/usr/bin/env python3
import re, yaml, datetime, math
from otterwiki.plugins import hookimpl, plugin_manager
from dateutil.relativedelta import relativedelta

DEFAULTCONFIG = """
# Format strings
# Supported format codes:
# %a    Weekday (abbr.)
# %A    Weekday
# %d    Day of the month (0-padded)
# %-d   Day of the month
# %b    Month (abbr.)
# %B    Month
# %m    Month (0-padded)
# %-m   Month
# %Y    Year
# %+Y   Year (with CE/BCE), custom property!
date_format_y: "%+Y"
date_format_ym: "%B %+Y"
date_format_ymd: "%B %-d, %+Y"
age_format: "(age %~AGE)" # %~AGE -> age in years

# Current time config
use_real_time: false
current_time: "372-2-12" # Fantasy time, format: y-m-d

# Fantasy time system configuration
suffix_bce: BCE
suffix_ce: CE
months:
  - name: "Spring"
    name_short: "Spr"
    days: 90
  - name: "Summer"
    name_short: "Sum"
    days: 90
  - name: "Fall"
    name_short: "Fal"
    days: 90
  - name: "Winter"
    name_short: "Win"
    days: 90
weekdays: [Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday]
weekdays_short: [Mon, Tue, Wed, Thu, Fri, Sat, Sun]
weekday_offset: 0 # The system understands ymd 0-1-1 to be the first weekday, offset by this variable
"""

class DatePlugin:
    date_tags = re.compile(r"`date-?(?P<age>age)? (?P<year>\d+)-?(?P<month>\d+)?-?(?P<day>\d+)?`")
    config_file = "date_config.yaml"

    def get_year_cebce(self, year: int, config) -> str:
        if config["use_real_time"]:
            return f"{abs(year)} {'BCE' if year < 0 else 'CE'}"
        
        suffix = config['suffix_bce'] if year < 0 else config['suffix_ce']
        return f"{abs(year)}{' ' if suffix != '' else ''}{suffix}"

    def strftime_fantasy(self, fstring: str, config, year, month, day):
        month = month if month != None else 1
        day = day if day != None else 1

        days_per_year = sum(m["days"] for m in config["months"])
        weekday = (config["weekday_offset"] + year * days_per_year + day)
        for i, m in enumerate(config["months"]):
            if i + 1 == month:
                break
            weekday += m["days"]
        weekday = weekday % len(config["weekdays"])
        
        fstring = fstring.replace("%a", config["weekdays_short"][weekday])
        fstring = fstring.replace("%A", config["weekdays"][weekday])
        fstring = fstring.replace("%d", str(day).zfill(int(math.log(config["months"][month-1]["days"], 10))))
        fstring = fstring.replace("%-d", str(day))
        fstring = fstring.replace("%b", config["months"][month-1]["name_short"])
        fstring = fstring.replace("%B", config["months"][month-1]["name"])
        fstring = fstring.replace("%m", str(month).zfill(int(math.log(len(config["months"]), 10))))
        fstring = fstring.replace("%-m", str(month))
        fstring = fstring.replace("%Y", str(year))
        fstring = fstring.replace("%+Y", self.get_year_cebce(year, config))

        return fstring

    def get_age_fantasy(self, config, year, month, day):
        month = month if month != None else 1
        day = day if day != None else 1

        current_time = config["current_time"].split("-")

        age = (int(current_time[0]) - year) - 1
        if (month < int(current_time[1])) or (month == int(current_time[1]) and day <= int(current_time[2])):
            age += 1

        return age

    @hookimpl
    def setup(self, app, db, storage):
        self.storage = storage
        if not storage.exists(self.config_file):
            storage.store(
                self.config_file,
                DEFAULTCONFIG,
                "Create default config for date_timeline plugin."
            )

    @hookimpl
    def renderer_markdown_preprocess(self, md: str) -> str | None:
        config = yaml.safe_load(self.storage.load(self.config_file))

        def repl(m: re.Match) -> str:
            groups = m.groupdict()
            include_age = groups["age"] != None
            year = int(groups["year"])
            month = int(groups["month"]) if groups["month"] != None else None
            day = int(groups["day"]) if groups["day"] != None else None

            format_string = config["date_format_y"]
            if month != None:
                format_string = config["date_format_ym"]
            if day != None:
                format_string = config["date_format_ymd"]

            if config["use_real_time"]:
                date = datetime.datetime(year, month if month != None else 1, day if day != None else 1)
                now = datetime.datetime.now()
                output =  date.strftime(format_string)
                if include_age:
                    output += " " + config["age_format"].replace("%~AGE", str(relativedelta(now, date).years))
                return output.replace("%+Y", self.get_year_cebce(year, config))

            fantasy_age = self.get_age_fantasy(config, year, month, day)

            return self.strftime_fantasy(format_string + f" {config['age_format'].replace('%~AGE', str(fantasy_age)) if include_age else ''}", config, year, month, day)

        return self.date_tags.sub(repl, md)

plugin_manager.register(DatePlugin())