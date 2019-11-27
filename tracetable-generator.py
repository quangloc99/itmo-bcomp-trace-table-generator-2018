import argparse
import asyncio
import csv
import math
import os
import sys
from asyncio import subprocess
from itertools import zip_longest
from pprint import PrettyPrinter


class SubprocessInteractor:
    def __init__(self, *subprocess_args):
        self.subprocess_args = subprocess_args
        self.subprocess = None
        self.debug = False

    async def init_subprocess(self):
        self.subprocess = await asyncio.create_subprocess_exec(*self.subprocess_args,
                                                               stdin=subprocess.PIPE,
                                                               stdout=subprocess.PIPE)
        return self

    async def readline(self, timeout=math.inf, name="subprocess"):
        try:
            s = (await asyncio.wait_for(self.subprocess.stdout.readline(), timeout=timeout)).decode("UTF-8")
            if self.debug:
                print("%s: %s" % (name, s), end="", file=sys.stderr)
            return s
        except asyncio.TimeoutError:
            return None

    async def writeln(self, msg, name="Client"):
        if self.debug:
            print("%s: %s" %  (name, msg), file=sys.stderr)
        self.subprocess.stdin.write((msg + "\n").encode())
        await self.subprocess.stdin.drain()


class AsmCompilationError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class RunningError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class BcompInteractor(SubprocessInteractor):
    def __init__(self, path_to_bcomp):
        super(BcompInteractor, self).__init__("java", "-Dmode=cli", "-jar", path_to_bcomp)

    async def readline(self, timeout=math.inf, name="Bcomp"):
        return await super(BcompInteractor, self).readline(timeout=timeout, name=name)

    async def safe_readline(self, exception, timeout=math.inf):
        s = await self.readline(timeout=timeout)
        if s is not None and "Ошибка" in s:
            raise exception(s[9:])
        return s

    async def write_asm(self, program_texts, timeout=.5):
        await self.writeln("ASM")
        await self.readline()   # bcomp will say: "Введите текст программы. Для окончания введите END"
        for s in program_texts:
            await self.writeln(s)
        await self.writeln("END")
        s = await self.safe_readline(AsmCompilationError)
        assert(s is not None)

        start_addr = int(s.split()[-1], 16)

        # check if the program has result (has variable R)
        s = await self.readline(timeout=timeout)
        if s is None:
            return start_addr, -1
        result_addr = int(s.split()[-1], 16)
        return start_addr, result_addr

    async def read_trace(self):
        header = (await self.safe_readline(RunningError)).split()
        values = (await self.safe_readline(RunningError)).split()
        # print(values, file=sys.stderr)
        d = {}
        for k, v in zip_longest(header, values):
            # some headers's names may be conflicted.
            while k in d:
                k += "_"
            d[k] = v
        return d

    async def run_cmd_with_trace(self, cmd):
        await self.writeln(cmd)
        return await self.read_trace()

    async def move_command_counter_to(self, addr):
        return await self.run_cmd_with_trace(hex(addr)[2:].zfill(3) + " a")

    async def run_program(self, timeout=.1, on_new_line=None):
        table = []
        while True:
            await asyncio.sleep(timeout)  # Feeding too much commands at the same time cause some error. So wait a bit.
            table.append(await self.run_cmd_with_trace("c"))
            if on_new_line is not None:
                await on_new_line(table[-1])
            if table[-1]["РК"] == "F000":
                break
        return table

    async def turn_on_io(self, addr):
        await self.writeln("flag " + str(addr))
        s = (await self.readline()).split()
        return (s[3], s[-1])

    async def get_io(self, addr):
        await self.writeln("io " + str(addr))
        s = (await self.readline()).split()
        return (s[3], s[-1])

    async def set_io(self, addr, value):
        await self.writeln("io " + str(addr) + " " + str(value))
        s = (await self.readline()).split()
        return (s[3], s[-1])


async def main():
    try:
        global arg_parser
        args = arg_parser.parse_args()
        # print(args)

        if not os.path.isfile(args.bcomp_path):
            print(args.bcomp_path + " does not exists.", file=sys.stderr)
            sys.exit(1)

        bcomp = await BcompInteractor(args.bcomp_path).init_subprocess()
        bcomp.debug = args.debug

        # skip the intro
        while await bcomp.readline(timeout=args.timeout) is not None:
            pass

        # read the input
        start_addr, result_addr = await bcomp.write_asm(args.inp.readlines(), timeout=args.timeout)
        await bcomp.move_command_counter_to(start_addr)


        # TODO: manipulate with io 2
        await bcomp.turn_on_io(1)
        async def when_new_line(line):
            if line['РК'][:2] == 'E0':
                io_addr = int(line['РК'][-1])
                flag, value = await bcomp.turn_on_io(io_addr)
                if io_addr == 1:
                    (args.vu1 if args.vu1 is not None else sys.stdout).write(str(value) + "\n")

        trace_table = await bcomp.run_program(timeout=args.timeout, on_new_line=when_new_line)

        # well, write the output
        fields = ["Адр", "Знчн", "СК", "РА", "РК", "РД", "А", "C", "Адр_", "Знчн_"]
        writer = csv.DictWriter(args.out, fieldnames=fields, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(trace_table)

        # await writeln(hex(result_addr)[2:].zfill(3) + " a")
        # pp.pprint(await readTrace())
        # await writeln("r")
        # pp.pprint(await readTrace())

        await bcomp.writeln('exit')
    except (AsmCompilationError, RunningError) as e:
        print("Error while running bcomp: %s" % e, file=sys.stderr)
        return


if __name__ == "__main__":
    pp = PrettyPrinter(indent=2)
    arg_parser = argparse.ArgumentParser(
        description="A script that take a \"basic computer\" (bcomp)'s asm code and generate its tracetable in csv format."
                    "This script requires bcomp.jar program that can be found on se.ifmo.ru. "
    )
    arg_parser.add_argument("-i", "--inp", type=argparse.FileType('r'), default=sys.stdin,
                            help="Input file name. Default is stdin.")
    arg_parser.add_argument("-o", "--out", type=argparse.FileType('w'), default=sys.stdout,
                            help="Output file name. Default is stdout.")
    arg_parser.add_argument("-d", "--debug", action="store_true", default=False,
                            help="Turn on debug mode. If debug mode is turned on, then the script will print the interaction"
                                 " between it and the bcomp program to stderr.")
    arg_parser.add_argument("--bcomp-path", default="./bcomp.jar",
                            help="Path to bcomp.jar. Helpful when the bcomp.jar is in difference directory. "
                                 "Default is ./bcomp.jar.")
    arg_parser.add_argument("-t", "--timeout", type=float, default=.3,
                            help="The time to wait for bcomp's response (in seconds). "
                                 "Please note that if the timeout is too high, then the completion time will also be long. "
                                 "But if the timeout is too short, then it may not catch the bcomp's response and that will "
                                 "cause some error. Default is 0.3.")
    arg_parser.add_argument("--vu1", type=argparse.FileType('w'), default=sys.stdout,
                            help="Set this flag to set the file output for VU1."
                                 "The vu1 flag of BEVM is immediately set in the beginning and when the flag is clear.")
    # arg_parser.print_help()
    asyncio.get_event_loop().run_until_complete(main())
