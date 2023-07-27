# Hey there, if you haven't read thoughts.txt yet, you should read that first.
# That will explain why there are so many comments here too.

import sys, re
import pprint

pp = pprint.PrettyPrinter(indent=4)

def is_valid_handoff_type(type):
    return type in ("BOT", "OUTPUT")

#
# I'm going to use a class so that I don't store my state globally
#
class ChipFactory:

    def __init__(self):
        # Using dicts here so that I don't have to worry about process order
        # and missing indices
        self.processed_bots = {}
        self.pending_bots = {}
        self.outputs = {}
        # Not going to store input as that's not really needed

    def process_pending_bots(self):
        # I'm doing this in a really not scalable way right now; this first version.
        # I'm fine with talking scalability when we go over this.
        last_len = 0
        # Keep going until we get stuck. (We shouldn't with the input data from the assignment)
        while len(self.pending_bots) != last_len:
            last_len = len(self.pending_bots)

            # Converting to a list here to avoid an error.
            # The dict will be changed during iteration, but that is ok in our use case.
            keys = list(self.pending_bots.keys())
            for k in keys:
                bot = self.pending_bots[k]

                if len(bot["chips"]) != 2: continue # Bot isn't ready yet
                low_target = bot["low_target"]
                high_target = bot["high_target"]

                if low_target["type"] == "BOT":
                    self.give_chip_to_pending_bot(low_target["id"], min(bot["chips"]))
                elif low_target["type"] == "OUTPUT":
                    self.put_chip_in_output_bin(low_target["id"], min(bot["chips"]))

                if high_target["type"] == "BOT":
                    self.give_chip_to_pending_bot(high_target["id"], max(bot["chips"]))
                elif high_target["type"] == "OUTPUT":
                    self.put_chip_in_output_bin(high_target["id"], max(bot["chips"]))

                # Move to processed
                self.processed_bots[k] = bot

                # I'd be extra careful if this was something like C++,
                # But since we're iterating using a key list and keys are unique
                # I'm not too worried about this.
                del self.pending_bots[k]

        # This assumes the file follows all the rules that we figure out in thoughts.txt

        if len(self.pending_bots) > 0:
            raise Exception("Could not empty pending bots queue. Incomplete information?")


    def set_bot_intention(self, bot_id, low_type, low_id, high_type, high_id):
        '''
        Defines a bot and its intentions. Where does it want to put its highs and lows?

        @param bot_id       ID for the bot that we're defining. Has to be unique
        @param low_type     'BOT' | 'OUTPUT' target type for the low value
        @param low_id       target id for the low value
        @param high_type    'BOT' | 'OUTPUT' target type for the high value
        @param high_id      target id for the high value
        '''
        # If this were an actual product I'd write errors that detail the
        # offending input values.
        if not is_valid_handoff_type(low_type): raise Exception("Low handoff type is invalid")
        if not is_valid_handoff_type(high_type): Exception("Low handoff type is invalid")
        bot = self.get_or_create_pending_bot(bot_id)
        if bot["low_target"] is not None: raise Exception("Low handoff type is invalid")
        if bot["high_target"] is not None: raise Exception("High handoff type is invalid")

        bot["low_target"] = {
            "type": low_type,
            "id": low_id,
        }
        bot["high_target"] = {
            "type": high_type,
            "id": high_id,
        }

        # I really miss explicit reference types in Python
        # I end up being really cautious because of that.
        # I've seen this go wrong.
        self.pending_bots[bot_id] = bot

    # The bot should have probably been a class.
    # But limited time, can't fret over those details.

    def get_or_create_pending_bot(self, bot_id):
        return self.pending_bots.setdefault(bot_id, {
            "low_target": None,
            "high_target": None,
            "chips": []
        })

    def give_chip_to_pending_bot(self, bot_id, chip_id):
        bot = self.get_or_create_pending_bot(bot_id)
        bot["chips"].append(chip_id)

        if len(bot["chips"]) > 2: raise Exception("Bot was given more than two chips.") # Bots can only have two chips

        self.pending_bots[bot_id] = bot

    def put_chip_in_output_bin(self, output_bin, chip_id):
        # Treating output bin as being able to hold multiple outputs right now.
        # Makes it easier to see if two chips ended up in one bin, since that shouldn't happen.
        self.outputs.setdefault(output_bin, [])
        self.outputs[output_bin].append(chip_id)


if __name__ == "__main__":
    # Could add nice argument handling using argparse here. Won't be doing because of limited time.
    # My opinions: short args are nice (think -i), but you need to allow long args (think --input)
    # Long arguments are good for automation since it becomes easier to read orchestrating scripts.
    filename = sys.argv[1]

    # Triple quoting the regexes here so I don't have to double escape the escape sequences
    # Using \s+ instead of direct spaces to support slightly different formatted output.
    # Not really needed here, but I felt that including it demonstrates care for edge cases.
    # I would also prefer to define these as CAPITAL_SNAKE_CASE constants at the top of the file.

    # https://regex101.com/r/sfaweJ/1
    bot_handoff_pattern = r"""^\s*bot\s+(?P<bot_id>\d+)\s+gives\s+(?P<target1_low_high>[a-z]+)\s+to\s+(?P<target1_type>[a-z]+)\s+(?P<target1_id>\d+)\s+and\s+(?P<target2_low_high>[a-z]+)\s+to\s+(?P<target2_type>[a-z]+)\s+(?P<target2_id>\d+)"""

    # https://regex101.com/r/binrE7/1
    bot_input_pattern = r"""^value\s+(?P<value>\d+)\s+goes\s+to\s+bot\s+(?P<bot_id>\d+)"""

    factory = ChipFactory()

    with open(filename, 'r') as file:
        for line in file.readlines():
            handoff_data = re.match(bot_handoff_pattern, line)

            if handoff_data is not None:
                bot_id = int(handoff_data.group("bot_id"))

                # This could have been cleaner, but this works

                target1_low_high = handoff_data.group("target1_low_high")
                target1_type = handoff_data.group("target1_type")
                target1_id = int(handoff_data.group("target1_id"))

                target2_low_high = handoff_data.group("target2_low_high")
                target2_type = handoff_data.group("target2_type")
                target2_id = int(handoff_data.group("target2_id"))

                if target1_low_high == target2_low_high: raise Exception("one instruction has two high or two low targets")

                # Not a fan of how messy this came out

                low_type = (target1_type if target1_low_high == "low" else target2_type).upper()
                high_type = (target1_type if target1_low_high == "high" else target2_type).upper()
                low_id = (target1_id if target1_low_high == "low" else target2_id)
                high_id = (target1_id if target1_low_high == "high" else target2_id)

                factory.set_bot_intention(bot_id, low_type, low_id, high_type, high_id)

                continue

            bot_input_data = re.match(bot_input_pattern, line)

            if bot_input_data is not None:
                value = int(bot_input_data.group("value"))
                bot_id = int(bot_input_data.group("bot_id"))

                factory.give_chip_to_pending_bot(bot_id, value)

                continue

    # Time process. This is what we've been waiting for!

    factory.process_pending_bots()

    # Using Pretty print here for convience
    # I don't want to print a custom format

    print("Output bins")
    pp.pprint(factory.outputs)

    print("Processed Bots")
    pp.pprint(factory.processed_bots)
