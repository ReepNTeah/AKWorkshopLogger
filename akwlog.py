#!python
import argparse
import csv
from datetime import date
from pathlib import Path
import re
import sys

# Last progress: Added the last column in the report function. Find a way to make another attribute in the operatorstatistics class to show the most processed material.
OPLIST_DIR = Path.home() / 'aklogs' / 'oplist.txt'
LOG_DIR = Path.home() / 'aklogs' / 'wslogs.csv'

TEST_SHOW_O = ['show', '-o']


def get_file_contents(file_dir):
    """
        file_dir: Path object pointing to plaintext.

        Returns a File object containing a list of strings containing each line in the file, or None if it does not exist.
    """
    try:
        with open(file_dir) as file:
            return [row for row in csv.DictReader(file)]
    except:
        print("The file does not exist or cannot be read.")
        sys.exit(1)


def main():

    parser = argparse.ArgumentParser(
        description="Logs workshop attempts in your /homedir/aklogs folder.")
    subparser = parser.add_subparsers()

    parser_wlog = subparser.add_parser('wlog', help='Log a workshop attempt.')
    parser_wlog.add_argument("op", help="Operator name", type=str)
    parser_wlog.add_argument("mat", help="Material processed", type=str)
    parser_wlog.add_argument(
        "-amt", help="Amount of material processed (defaults to 1)", nargs='?', default=1, type=int)
    parser_wlog.add_argument(
        "-byp", help="Byproducts produced (defaults to none)", nargs='*', default=[], type=str)
    parser_wlog.set_defaults(func=log_attempt)

    parser_show = subparser.add_parser(
        'show', help="Shows the stats for the operator or materials.")
    parser_show.add_argument(
        '-opstats', action="store_true", default=False)
    parser_show.set_defaults(func=show_handler)

    # args = parser.parse_args(TEST_SHOW_O)
    args = parser.parse_args()
    args.func(args)

    sys.exit(0)


def show_handler(args):
    if args.opstats == True:
        show_operator_statistics()
    else:
        print("Opstats:", args.opstats)
        pass


def fix_eof(filestream):
    """
        filestream: Writeable File object opened in plaintext.

        Appends a newline if EOF is not a newline.
    """
    if filestream.tell() == 0:
        return
    else:
        filestream.seek(filestream.tell()-1, 0)
        if filestream.read() != '\n':
            print('\n', end='', file=filestream)


def log_attempt(args):
    """
        Logs the entered workshop process attempt into home/aklogs/wslogs.txt with a timestamp.
        args: a namespace that contains op, mat, amt, byp
        fields: an iterable denoting the columns on the log
        log_dir: Path object to file

        Return: None.
    """

    is_valid, invalidity = is_valid_input(args)

    if is_valid:
        fields = ('Operator', 'Material', 'Amount', 'Byproducts', 'Timestamp')

        with open(LOG_DIR, 'a+', newline='\n') as logs:

            fix_eof(logs)

            writer = csv.DictWriter(logs, fieldnames=fields)

            if logs.tell() == 0:
                writer.writeheader()

            writer.writerow(
                {fields[0]: args.op.title(),
                 fields[1]: args.mat,
                 fields[2]: args.amt,
                 fields[3]: f"{' '.join(args.byp)}",
                 fields[4]: date.today().strftime("%d-%m-%Y")})

        print("Log successful.")
    else:
        print("Invalid input:", invalidity)


def is_valid_input(args):
    """
        Returns a tuple containing a Boolean and a string message of invalidity.
    """
    # Possible invalid inputs include:
    # - The operator does not exist
    # - The material does not exist
    # - The byproducts are greater than the processed amount - Done

    if len(args.byp) > args.amt:
        return (False, "More byproducts than amount processed.")
    elif does_mats_exist(args.mat) == False:  # check if mats exist
        return(False, "Material does not exist")
    else:
        return (True, "")


def does_mats_exist(material):
    matsFile = 'mats.txt'
    matsData = get_file_contents(matsFile)
    matsList = []
    for item in matsData:
        matsList.append(
            Material(item['alias'], item['name'], item['submats'].split(' ')))
    for mat in matsList:
        if material == mat.name:
            return True
    return False
    # Read the entire log file of mats
    # Check if material exists from the logfile of mats
    # Return true or false


# Create a function that prints statistics based on the log file.
# Operator                          - Done
# Number of products processed      - Done
# Number of byproducts produced     - Done
# Theoretical rate                  - Done
# Actual rate                       - Done
# Number of most processed product  - Done
# Number of most produced byproduct - Done
# Total sanity spent                - In progress

def show_operator_statistics():
    """
        log_dir: A Path object that points to the log file.
        op_dir: A Path object that points to the operator list file.

        Prints a table of statistics for each operator's performance in the workshop.
        Return: None
    """
    logs = get_file_contents(LOG_DIR)

    statistics = set_op_dict(logs)
    row = (13, 8, 12, 7, 8, 15, 10)
    print("Operator Stats".center(75, '='))  # Title
    print("Operator".ljust(row[0]),          # Columns
          "AmtProc".ljust(row[1]),
          "Byproducts".ljust(row[2]),
          "TRate".ljust(row[3]),
          "ARate".ljust(row[4]),
          "TopProcessed".ljust(row[5]),
          "TopByproduct".ljust(row[6]),
          sep='')
    for op in statistics:
        opstats = statistics[op].printed_stats()
        print(
            opstats[0].ljust(row[0]),       # Name
            opstats[1].ljust(row[1]),       # Amount processed
            opstats[2].ljust(row[2]),       # Byproducts produced
            opstats[3].ljust(row[3]),       # Theoretical rate
            opstats[4].ljust(row[4]),       # Actual rate
            opstats[5].ljust(row[5]),       # Top processed material
            opstats[6].ljust(row[6]),       # Top byproduct produced
            sep='')


def set_op_dict(logs):
    """
        op_dir: Path object to operator list.
        logs: A File object containing the logs for workshop processes.

        Returns a dictionary in the shape of {'Operator', Operator()}.
    """
    stats_dict = {}
    op_list = get_file_contents(OPLIST_DIR)

    for op in op_list:
        stats_dict.setdefault(
            op['Operator'], Operator(op['Operator'], op['Bonus Rate']))

    for log in logs:
        operator = log['Operator']
        stats_dict[operator].add_processed_amount(
            log['Material'], int(log['Amount']))
        stats_dict[operator].set_byproducts(log['Byproducts'])

    return stats_dict


class Operator:
    def __init__(self, name, brate):
        """
            Creates an Operator object.
        """
        self.name = name
        self.trate = round((0.1 + float(brate)*0.1)*100, 2)
        self.nproc = 0
        self.nbyp = 0
        self.arate = 0
        self.matprocs = {}
        self.byps = {}

    def __str__(self):
        return f'Operator(name={self.name},nproc={self.nproc},nbyp={self.nbyp},trate={self.trate},arate={self.arate})'

    # You should make a self-describing method, someday.

    # def __repr__(self):
    #     return (f'OpStats(nproc={self.nproc}, ',
    #             f'nbyp={self.nbyp}, ',
    #             f'trate={self.trate}, ',
    #             f'arate={self.arate})',
    #             f'{self.matprocs}')

    def add_processed_amount(self, processed, amount):
        """
            Adds to the operator's total byproduct amount.
        """
        self.add_material(self.matprocs, processed, amount)
        self.nproc += amount

    def set_byproducts(self, byproducts):
        """
            Counts the number of byproducts in the iterable and adds it to the operator's total byproducts produced.
        """
        bypList = byproducts.split(' ')

        for item in byproducts:
            self.add_material(self.byps, item)

        self.nbyp += len(bypList)

        self.get_arate()

    def printed_stats(self):
        """
            Returns a tuple of strings containing the operator's theoretical rate, number of processed mats, byproducts, and its current, actual rate.
        """
        return (self.name, str(self.nproc), str(self.nbyp), f'{self.trate}%', f'{self.arate}%', self.get_topmat(self.matprocs), self.get_topmat(self.byps))

    def get_arate(self):
        """
            Recalculates the actual rate of the object.
        """
        self.arate = round(self.nbyp / self.nproc * 100, 2)

    @staticmethod
    def add_material(dict, material, amount=1):
        """
            dict: Dict{'MaterialName': int}
            material: str

            Adds material to dict.
        """
        if dict.setdefault(material, amount) != amount:
            dict[material] += amount

    @staticmethod
    def get_topmat(matDict):
        """
            Returns a string of the most processed byproduct. If there is more than one top product, returns "More than 1".
        """
        if not matDict:
            return "No materials"
        topmat = ['None', 0]
        for byp, num in matDict.items():
            if num > topmat[1]:
                topmat = [byp, num]
            elif num == topmat[1]:
                return 'More than 1'
        return f'{topmat[0]}({topmat[1]})'


class Material:
    def __init__(self, alias, name, submats):
        """
            name: string of material name.
            tier: int, 1-5
            submats: dict() of {string: int}
        """
        self.alias = alias[:-1]
        self.name = str(name)
        self.tier = int(alias[-1:])
        self.submats = {aliased[1:]: int(aliased[:1]) for aliased in submats}

    def __str__(self):
        return f'Material(name={self.name}, tier={self.tier}, submats={self.submats})'

    def __repr__(self):
        return f'{self.name}, {self.tier}, {[name for name in self.submats.items()]}'


if __name__ == "__main__":
    main()
