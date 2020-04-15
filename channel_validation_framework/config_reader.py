class ConfigData():
    stimulus = {}

    def __str__(self):
        print("Data: ")
        print(self.channel_name)
        print(self.channel_data)
        print(self.stimulus)
        return ""





    def extract_steps_from_stimulus(self, stimulus_name):
        t = []
        v = []
        n = 1


        if stimulus_name in self.stimulus.keys():
            map0 = self.stimulus[stimulus_name]
            while "vhold" + str(n) and "thold" + str(n) in map0.keys():
                t.append(map0["thold" + str(n)])
                v.append(map0["vhold" + str(n)])
                n += 1
            return t, v
        else:
            print("\"" + type + "\" does not exist as stimulus in the config file")






# Just to wrap the parsing functions
class ConfigReader():
    # Parse a block {} and return a dictionary of key:value
    def parse_block(file_object):
        map0 = {}
        record = False
        line = file_object.readline()
        while line:
            parsed_line = line.split()
            if (len(parsed_line)):
                if parsed_line[0] == '{':
                    record = True
                elif parsed_line[0] == '}':
                    break
                elif record and len(parsed_line) == 2:
                    try:
                        map0[parsed_line[0]] = float(parsed_line[1])
                    except:
                        try:
                            map0[parsed_line[0]] = [float(item) for item in parsed_line[1].split(':')]
                        except:
                            map0[parsed_line[0]] = parsed_line[1]

            line = file_object.readline()
        return map0

    # Read the file and parse as supposed by the class ConfigData
    def parse_file(filepath):
        data = ConfigData()
        with open(filepath, 'r') as file_object:
            line = file_object.readline()
            while line:
                parsed_line = line.split()
                if len(parsed_line) == 2 :
                    if parsed_line[0] == "Channel" :
                        map0 = ConfigReader.parse_block(file_object)
                        data.channel_name = parsed_line[1]
                        data.channel_data = map0
                    elif parsed_line[0] == "Stimulus" :
                        map0 = ConfigReader.parse_block(file_object)
                        data.stimulus[parsed_line[1]] = map0


                line = file_object.readline()
        return data