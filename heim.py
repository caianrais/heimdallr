#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# There are standard libraries and should not fail
import sys
import socket
import textwrap

from argparse import ArgumentParser
from argparse import RawTextHelpFormatter


# 3rd-party libraries
try:
    import boto3

    from tabulate import tabulate

except ImportError as e:
    print('Impossible to import 3rd-party libraries.\n'
          'Latest traceback: {0}' . format(e.args[0]))
    sys.exit(1)


__PROGRAM__ = 'heimdallr'


class CLI:
    _parser = None

    def __init__(self):
        self._parser = ArgumentParser(
                    prog=__PROGRAM__,
                    formatter_class=RawTextHelpFormatter,
                    description=textwrap.dedent('''\
                            ** heimdallr - the aws ec2 port checker **

                            heimdallr is a command-line utility written in
                            python3 that checks if a given tcp port is being
                            listened by your ec2 instances. By default, the
                            utility searches for all running instances, though
                            you can filter by the "Name" tag.
                            '''),
                    epilog=textwrap.dedent('''\
                            Example:

                                $ heim -p 10050 -t 'prd'
                                # => In all ec2 instances where tag 'Name'
                                     equals 'prd', checks if the tcp port 10050
                                     is open.
                            '''))

        self._parser.add_argument(
                '-p', '--port',
                action='store',
                dest='port',
                metavar='num',
                nargs=1,
                type=int,
                help=textwrap.dedent('''\
                        the tcp port the utility will check
                        against (default: 22 (SSH))
                        '''))

        self._parser.add_argument(
                '-t', '--tag',
                action='store',
                dest='tag',
                metavar='name',
                nargs=1,
                type=str,
                help=textwrap.dedent('''\
                        filters the checkage by the value
                        defined in 'Name' tag
                        '''))

    def act(self):
        return self._parser.parse_args()


class AWS:
    @staticmethod
    def get_ec2_ip_list(tag_value):
        aws_ec2 = boto3.client('ec2')

        filters = []

        if tag_value:
            filters.append({'Name': 'tag:Name', 'Values': [tag_value]})

        filters.append({'Name': 'instance-state-name', 'Values': ['running']})

        response = aws_ec2.describe_instances(Filters=filters)

        instance_ips = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_ips.append(instance['PublicIpAddress'])

        return instance_ips

    @staticmethod
    def is_open(ip, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            sock.settimeout(5)
            sock.connect((ip, port))
            return True

        except socket.error:
            return False


def main():
    cli = CLI()
    argp = cli.act()

    print('\nFetching your data, hang tight...\n')

    port = 22
    if argp.port:
        port = argp.port[0]

    tag_value = ''
    if argp.tag:
        tag_value = argp.tag[0]

    ip_list = AWS.get_ec2_ip_list(tag_value)

    lines = []
    for ip in ip_list:
        stat = 'No'
        if(AWS.is_open(ip, port)):
            stat = 'Yes'

        lines.append([ip, port, stat])

    if len(lines) > 0:
        print(tabulate(lines, headers=['IP', 'Port', 'Is Open?']))
    else:
        print('I couldn\'t find anything running.')

    sys.exit(0)


if __name__ == '__main__':
    main()
