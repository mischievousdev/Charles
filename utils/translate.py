import json
import os

def get_text(guild, file, data):
    try:
        with open(f"db/guilds/{guild.id}.json", "r") as f:
            lang = json.load(f)

        lang_option = lang["Guild_Info"]["Language"]

        try:
            with open(f"db/Languages/{lang_option}/{file}.json", "r") as f:
                txt = json.load(f)

            try:
                return txt[data]
            except KeyError:
                with open(f"db/Languages/EN/{file}.json", "r") as f:
                    txt = json.load(f)

                return txt[data]

        except FileNotFoundError:
            with open(f"db/Languages/EN/{file}.json", "r") as f:
                txt = json.load(f)

            return txt[data]

    except Exception:
        with open(f"db/Languages/EN/{file}.json", "r") as f:
            txt = json.load(f)

        return txt[data]
