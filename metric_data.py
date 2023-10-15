class Metric_data:
    def __init__(self, metric) -> None:
        label = metric["Label"]

        print("original label:", label)

        if "cluster" in label:
            # the string is split into 3 parts when / is detected
            #       0      1      2
            # ex: "part 1/part 2/part 3"
            # takes the third part "part 3" at index 2 and assigns it to grouplabel
            self.grouplabel = label.split("/")[2]
            print("cluster step 1:", self.grouplabel)

            # take a string and split it by space and put them into an array
            # ex: "part 1/part 2/part 3"
            #    0       1       2       3
            # ["part","1/part","2/part","3"]
            label = label.split(" ")
            print("cluster step 2:", label)

            # pops the last element from that array and sets it to label
            # "3"
            label = label.pop()
            print("cluster step 3:", label)

        elif "AWS/ApplicationELB" in label:
            # take a string and split it by space and put them into an array
            # ex: "part 1/part 2/part 3"
            #    0       1       2       3
            # ["part","1/part","2/part","3"]
            # "3"
            label = "ApplicationELB-" + label.split(" ").pop()
            print("ELB:", label)

        else:
            # take a string and split it by space and put them into an array
            # ex: "part 1/part 2/part 3"
            #    0       1       2       3
            # ["part","1/part","2/part","3"]
            # "1/part"
            self.grouplabel = label.split(" ")[1]
            print("else:", self.grouplabel)

            # take a string and split it by space and put them into an array
            # ex: "part 1/part 2/part 3"
            #    0       1       2       3
            # ["part","1/part","2/part","3"]
            # "3"
            label = "EC2-" + label.split(" ").pop()
            print("else step 2:", label)

        self.label = label
        self.timestamps = metric["Timestamps"]
        self.values = metric["Values"]
