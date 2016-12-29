#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple unofficial get-only API and python tool for jenkins."""

__author__ = "Ole Herman Schumacher Elgesem"

import requests
import json
from os.path import exists
import os
from sys import exit
from argparse import ArgumentParser
from time import sleep
from collections import OrderedDict

def job_created(name):
    print("Job created: " + name)

def job_deleted(name):
    print("Job deleted: " + name)

def build_passed(name):
    print("Build passed: " + name)

def build_failed(name):
    print("Build failed: " + name)

def build_started(name):
    print("Build started: " + name)

def build_aborted(name):
    print("Build aborted: " + name)

# Mostly useful for debugging
def unknown_colors(name, old_color, new_color, verbose=True):
    if(verbose):
        print("Unrecognized color change: {} {}->{}".format(name, old_color, new_color))

def write_file(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(data)
    except:
        print("Could not write to '{}'".format(path))

def load_json(path):
    with open(path, "r") as f:
        d = json.load(f, object_pairs_hook = OrderedDict)
    return d

class Jenkins:
    @staticmethod
    def api_get(url):
        sleep(1)
        url = url +"/api/json/"
        response = requests.get(url)
        return json.loads(response.text)

    @staticmethod
    def get_jobs_url(url):
        dictionary = Jenkins.api_get(url)
        jobs = {}
        for job in dictionary["jobs"]:
            name = job["name"]
            color = job["color"]
            jobs[name] = color
        return OrderedDict(sorted(jobs.items()))

    def internal_get(self):
        if self.offline:
            return load_json(self.input_file)
        else:
            return Jenkins.get_jobs_url(self.url)

    def __init__(self, url = None, *, verbose = False, directory = ".", input_file = None, funcs = {},
                            func_job_created    = job_created,
                            func_job_deleted    = job_deleted,
                            func_build_passed   = build_passed,
                            func_build_failed   = build_failed,
                            func_build_started  = build_started,
                            func_build_aborted  = build_aborted,
                            func_unknown_colors = unknown_colors):
        if url is not None:
            while url[-1] == "/":
                url = url[:-1]
            if "http" not in url:
                url = "https://"+url
            self.url = url
            self.offline = False
        elif input_file is not None:
            self.input = input_file
            self.url = self.input
            self.offline = True
        else:
            print("Jenkins class must get either url or input_file as argument.")
            sys.exit(1)
        self.verbose = verbose
        self.directory = directory
        self.funcs = {}
        self.funcs["created"] = func_job_created
        self.funcs["deleted"] = func_job_deleted
        self.funcs["passed"]  = func_build_passed
        self.funcs["failed"]  = func_build_failed
        self.funcs["started"] = func_build_started
        self.funcs["aborted"] = func_build_aborted
        self.funcs["unknown"] = func_unknown_colors
        for name, func in funcs.items():
            self.funcs[name] = func

        self.jobs = None
        if self.directory:
            if not exists(self.directory):
                os.makedirs(self.directory, exist_ok=True)
            try:
                self.load_files()
            except FileNotFoundError:
                self.verbose_print("No files found for server {}.".format(self.url))

    def set_func(self, key, func):
        if key not in self.funcs:
            raise KeyError
        funcs[key] = func

    def verbose_print(self, msg):
        if self.verbose:
            print(msg)

    def print_running_jobs(self):
        print( "Running jobs:\n  " +
               "\n  ".join(self.get_running_jobs()) )

    def get_job_names(self):
        for name in self.jobs:
            yield name

    def get_running_jobs(self):
        for name, color in self.jobs.items():
            if "anime" in color:
                yield name

    def call(self, func_id, *args, **kwargs):
        try:
            self.funcs[func_id](*args, **kwargs)
            return func_id
        except:
            arg_list = []
            for a in args:
                arg_list.append(str(a))
            for k,v in kwargs.items():
                arg_list.append("{}={}".format(k,v))
            arg_string = ", ".join(arg_list)
            print("Function call failed: {}({})".format(func_id, arg_string))
            return "function-error"

    def status_change(self, name, old_color, new_color):
        if "anime" in new_color and "anime" not in old_color:
            return self.call("started", name)
        elif new_color == "aborted":
            return self.call("aborted", name)
        elif new_color == "red":
            return self.call("failed", name)
        elif new_color == "blue":
            return self.call("passed", name)
        else:
            return self.call("unknown", name, old_color, new_color, self.verbose)

    def get_jobs_json(self, *, indent=4, ensure_ascii=False):
        return json.dumps(self.jobs, indent=indent, ensure_ascii=ensure_ascii)

    def load_files(self, *, json_path="jenkins_jobs.json", txt_path="jenkins_server.txt"):
        with open(os.path.join(self.directory,txt_path), "r") as f:
            old_url = f.readline()
        if old_url != self.url:
            if self.verbose:
                self.verbose_print("URL changed - history was lost.")
                self.verbose_print("( {} != {} )".format(old_url, self.url))
        else:
            self.verbose_print("Jenkins URL matches: '{}'.".format(self.url))
            self.jobs = load_json(self.directory+json_path)
            self.verbose_print("Read previous status from '{}' succesfully.".format(json_path))

    def dump_all(self, *, json_path="jenkins_jobs.json", txt_path="jenkins_server.txt"):
        write_file(os.path.join(self.directory, json_path), self.get_jobs_json())
        write_file(os.path.join(self.directory, txt_path) , self.url)

    def offline_update(self, new_jobs):
        changes = OrderedDict()
        old_jobs = self.jobs
        for name in old_jobs:
            if name not in new_jobs:
                changes[name] = self.call("deleted", name)

        for name, new_color in new_jobs.items():
            if name not in old_jobs:
                changes[name] = self.call("created", name)
                continue
            old_color = old_jobs[name]
            if new_color != old_color:
                changes[name] = self.status_change(name, old_color, new_color)
        self.jobs = new_jobs

    def update(self):
        changes = None
        if not self.jobs:
            self.jobs = self.internal_get()
        else:
            new_jobs = self.internal_get()
            changes = self.offline_update(new_jobs)
        if self.directory:
            self.dump_all()
        return changes

if __name__ == "__main__":
    argparser = ArgumentParser(description= 'Get Jenkins status and generate events. '
                                            'Default behavior is to print changes in status since last run.')
    argparser.add_argument( '-l', '--loop',  help='Run in loop forever.',
                            action="store_true")
    argparser.add_argument( '--running', '-r', help='Print running jobs.',
                            action="store_true")
    argparser.add_argument( '-d', '--directory', help='Directory used for saving server url and json.',
                            type=str, default='./')
    argparser.add_argument( '-v', '--verbose',  help='More detailed output.',
                            action="store_true")
    argparser.add_argument( 'url', type=str,
                            help='Jenkins URL (example:"https://ci.cfengine.com/")')

    args = argparser.parse_args()
    if not args.directory and not args.loop and not args.running:
        print("Error: nothing to do. Use --help for more info.")
        exit(1)
    jenkins = Jenkins(args.url, verbose = args.verbose, directory = args.directory)
    jenkins.update()
    if args.running:
        jenkins.print_running_jobs()
    while args.loop:
        sleep(5)
        jenkins.update()
