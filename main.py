#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import subprocess
import sys

import dash
import dash_html_components as html
from dash.dependencies import Input, Output, State

from model import Model
import parser
from persistence import Data
from viewmodel import ViewModel
import view.layout as layout
from webapp import WebApp


CALLGRIND_PURE_FILE = Path('assets/callgrind_pure')
CALLGRIND_ANNOTATED_FILE = Path('assets/callgrind_annotated')


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary-path',
        type=Path,
        help='path to binary to be profiled')
    parser.add_argument('--callgrind-out-file',
        type=Path,
        help='path to callgrind output-file')

    return parser.parse_args(args)


def main(args):
    parsed_args = parse_args(args)
    if parsed_args.binary_path:
        subprocess.run([
            'valgrind',
            '--tool=callgrind',
            '--dump-instr=yes',
            '--dump-line=yes',
            '--callgrind-out-file={}'.format(str(CALLGRIND_PURE_FILE)),
            './{}'.format(str(parsed_args.binary_path))
        ])
        pipe = subprocess.Popen([
            'callgrind_annotate',
            '--threshold=100',
            '--inclusive=yes',
            '--tree=caller',
            str(CALLGRIND_PURE_FILE)
        ], stdout=subprocess.PIPE)
        text = pipe.communicate()[0].decode("utf-8")
        Path('testout').write_text(text)
        parsed_output = parser.parse_callgrind_output(text, 'main')
    else:
        parsed_output = parser.parse_callgrind_output(parsed_args.callgrind_out_file, 'main')
    data = Data(parsed_output)
    model = Model(data)
    view_model = ViewModel(model)
    WEB_APP = WebApp(view_model)
    WEB_APP.app.run_server(debug=True)


if __name__ == '__main__':
    main(sys.argv[1:])