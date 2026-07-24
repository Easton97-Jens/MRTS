#!/usr/bin/env python3

import argparse
import sys
import yaml
import string
import re
import copy
from ast import literal_eval
from itertools import product

from path_utils import existing_directory, path_within

NAME = "MRTS"
VERSION = "0.1"


class RuleGenerator(object):
    def __init__(self, flist, expdir, testdir):
        # set initial values
        self.version          = "%s/%s" % (NAME, VERSION)
        self.baseid           = 100000
        self.currid           = self.baseid
        self.templates        = []
        self.templates_dict   = {}
        self.default_operator  = "@rx"
        self.confdata         = {
            'target'       : None,
            'rulefile'     : None,
            'testfile'     : None,
            'templates'    : [],
            'colkey'       : [],
            'operator'     : self.default_operator,
            'oparg'        : "attack",
            'phase'        : [1,2,3,4],
            'actions'      : [],
            'directives'   : [],
            'constants'    : {},
            'generation'   : {},
            'phase_methods': {}
        }
        self.default_test_phase_methods = {
            1: "get",
            2: "post",
            3: "post",
            4: "post",
            5: "post"
        }

        self.default_constants = {}

        self.current_confdata = {}
        self.current_testdata = {}

        self.indent           = "    "
        self.indentdepth      = 0
        self.expdir           = existing_directory(expdir, "rules export directory")
        self.testdir          = existing_directory(testdir, "tests export directory")
        self.content          = ""
        self.testcontent      = {}

        self.re_tplvars  = re.compile(r"""\$\{[^ \n\t$,'"]*\}\$""")
        self.re_constants = re.compile(r"""~\{([^ \n\t$,'"]*)\}~""")

        self.testdict         = {
            'header': {
                'meta': {
                    'author': 'MRTS generate-rules.py',
                    'enabled': True,
                    'name': '',
                    'description': 'Desc'
                },
                'tests': []
            },
            'item': {
                'test_title': '',
                'ruleid': 0,
                'test_id': 0,
                'desc': '',
                'stages': [
                    {
                        'description': '',
                        'input': {
                            'dest_addr': '127.0.0.1',
                            'port': 80,
                            'protocol': 'http',
                            'method': '',
                            'headers': {
                                'User-Agent': 'OWASP MRTS test agent',
                                'Host': 'localhost',
                                'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5'
                            },
                            'uri': '/',
                            'version': 'HTTP/1.1'
                        },
                        'output': {
                            'log': {
                                'expect_ids': []
                            }
                        }
                    }
                ]
            }
        }

        # walk through the files and process them
        for f in flist:
            try:
                with open(f, 'r') as fp:
                    print("Processing file: %s" % (f))
                    t = yaml.safe_load(fp)
                    self.current_confdata = copy.deepcopy(self.confdata)
                    self.current_confdata['phase_methods'] = copy.deepcopy(self.default_test_phase_methods)
                    self.current_testdata = {}
                    self.parseconf(t)
                    self.content = ""
                    self.testcontent = {}
            except Exception as e:
                print("Can't open file: %s" % (f))
                print(", ".join(e.args))
                sys.exit(1)

    def parseconf(self, config):
        """Parse one configuration file and write its generated rule file."""
        config = self._replace_constants_if_needed(config)
        self._load_global_config(config)
        self._load_current_config(config)
        self._load_test_data(config)
        self._generate_configured_templates()
        self._generate_configured_objects(config)
        self._write_current_config()

    def _replace_constants_if_needed(self, config):
        if re.search(self.re_constants, str(config)) is None:
            return config
        return self.parseconstants(config)

    def _load_global_config(self, config):
        global_config = config.get('global')
        if global_config is None:
            return
        for key, value in global_config.items():
            if hasattr(self, key):
                setattr(self, key, value)
        for template in self.templates:
            self.templates_dict[template['name']] = template['template']

    def _load_current_config(self, config):
        for key in self.confdata:
            value = config.get(key)
            if value is not None:
                self.current_confdata[key] = value

    def _load_test_data(self, config):
        if 'testdata' in config:
            self.current_testdata = copy.deepcopy(config['testdata'])

    def _generate_configured_templates(self):
        for template_name in self.current_confdata['templates']:
            template = self.templates_dict.get(template_name)
            if template is None:
                print("No such template: %s" % (template_name))
                print("Avaliable templates: %s" % (", ".join(self.templates_dict.keys())))
                sys.exit(1)
            self.genrulefromtemplate(template, self.current_confdata)

    def _generate_configured_objects(self, config):
        for object_config in config.get('objects', []):
            self.genobject(object_config)

    def _write_current_config(self):
        if self.current_confdata['rulefile'] is not None:
            self.writeconf(self.content)

    def parseconstants(self, c):
        """Load and replace any used constants in current configuration"""
        # per-file local
        if 'constants' in c:
            self.current_confdata['constants'] = c['constants']
        # cross-file global
        if 'global' in c:
            if 'default_constants' in c['global']:
                self.default_constants = c['global']['default_constants']
            else:  # if no global constants, reset values defined under previous 'global' field
                self.default_constants = {}
        return self.swap_constants(c)

    def swap_constants(self, config):
        if isinstance(config, dict):
            return {key: self.swap_constants(value) for key, value in config.items()}
        if isinstance(config, list):
            return [self.swap_constants(value) for value in config]
        if isinstance(config, str):
            return self._swap_string_constants(config)
        return config

    def _swap_string_constants(self, value):
        for match in re.findall(self.re_constants, value):
            found, constant = self._find_constant(match)
            if found:
                value = self._replace_constant(value, match, constant)
        return value

    def _find_constant(self, name):
        if name in self.current_confdata['constants']:
            return True, self.current_confdata['constants'][name]
        if name in self.default_constants:
            return True, self.default_constants[name]
        return False, None

    def _replace_constant(self, value, name, constant):
        replacement = value.replace(f"~{{{name}}}~", str(constant))
        if isinstance(constant, (list, dict)):
            return literal_eval(replacement)
        return type(constant)(replacement)

    def genrulefromtemplate(self, template, current_confdata):
        """Generate rules and tests for every template argument combination."""
        template_data = self._build_template_data(template, current_confdata)
        generation_templates = self._build_generation_templates(template_data['generation'])
        rule_template = RuleGeneratorTemplate(template)
        template_data['currid'] = self.currid
        actions_defined = self._prepare_optional_macro(template_data, 'actions')
        directives_defined = self._prepare_optional_macro(template_data, 'directives')
        self._write_before_template(generation_templates.get('before'), template_data)
        for rule_data, colkeys, phase in self._rule_combinations(
                template_data, actions_defined, directives_defined):
            last_id = self._write_rule(
                rule_template,
                generation_templates,
                rule_data,
                directives_defined,
            )
            self._write_tests(colkeys, phase)
            self._advance_rule_id(directives_defined, generation_templates.get('after_each'), last_id)
        self._write_after_template(generation_templates.get('after'))

    def _build_template_data(self, template, current_confdata):
        variables = [
            variable.replace("${", "").replace("}$", "").lower()
            for variable in self.re_tplvars.findall(template)
        ]
        variables.extend(('colkey', 'generation'))
        return {
            variable: current_confdata[variable]
            if variable in current_confdata else getattr(self, variable)
            for variable in variables
            if variable in current_confdata or hasattr(self, variable)
        }

    def _build_generation_templates(self, generation):
        return {
            name: RuleGeneratorTemplate(generation[name])
            for name in ('before', 'after', 'before_each', 'after_each')
            if name in generation
        }

    def _prepare_optional_macro(self, template_data, name):
        if name in template_data:
            return True
        template_data[name] = [None]
        return False

    def _write_before_template(self, template, template_data):
        if template is None:
            return
        before = template.ruleid_substitute(
            increment_id_after_sub=True,
            **{'CURRID': template_data['currid']},
        ) + "\n"
        self.content += before
        self.currid = template.get_last_id()
        template_data['CURRID'] = self.currid

    def _rule_combinations(self, template_data, actions_defined, directives_defined):
        values = product(
            template_data['directives'],
            template_data['actions'],
            template_data['colkey'],
            template_data['operator'],
            template_data['oparg'],
            template_data['phase'],
        )
        for directive, action, colkeys, operator, operand, phase in values:
            rule_data = self._build_rule_data(
                template_data,
                directive,
                action,
                colkeys,
                operator,
                operand,
                phase,
                actions_defined,
                directives_defined,
            )
            yield rule_data, colkeys, phase

    def _build_rule_data(self, template_data, directive, action, colkeys, operator,
                         operand, phase, actions_defined, directives_defined):
        rule_data = copy.deepcopy(template_data)
        rule_data['target'] = self._target_for_colkeys(template_data['target'], colkeys)
        rule_data['operator'] = operator
        rule_data['oparg'] = operand
        rule_data['phase'] = phase
        if actions_defined:
            rule_data['actions'] = self.parseactions(action['action'])
        if directives_defined:
            rule_data['directives'] = self.parsedirectives(directive['directive'])
        return rule_data

    def _target_for_colkeys(self, target, colkeys):
        if len(colkeys) > 1:
            return "|".join("%s:%s" % (target, colkey) for colkey in colkeys)
        if len(colkeys) == 1 and colkeys[0] != '':
            return "%s:%s" % (target, colkeys[0])
        return "%s" % (target)

    def _write_rule(self, rule_template, generation_templates, rule_data, directives_defined):
        substitutions = {key.upper(): value for key, value in rule_data.items()}
        substitutions['CURRID'] = self.currid
        self._write_before_each(generation_templates.get('before_each'), substitutions)
        rule = rule_template.substitute(**substitutions) + "\n"
        last_id = self.currid
        if directives_defined:
            rule, last_id = self._substitute_directive_ids(rule, substitutions)
        self.content += rule
        return self._write_after_each(generation_templates.get('after_each'), substitutions, last_id)

    def _write_before_each(self, template, substitutions):
        if template is None:
            return
        before_each = template.ruleid_substitute(
            increment_id_after_sub=True,
            **substitutions,
        ) + "\n"
        self.content += before_each
        self.currid = template.get_last_id()
        substitutions['CURRID'] = self.currid

    def _substitute_directive_ids(self, rule, substitutions):
        directive_template = RuleGeneratorTemplate(rule)
        substituted_rule = directive_template.ruleid_substitute(**substitutions)
        return substituted_rule, directive_template.get_last_id()

    def _write_after_each(self, template, substitutions, last_id):
        if template is None:
            return last_id
        after_each = template.ruleid_substitute(**substitutions) + "\n"
        self.content += after_each
        return template.get_last_id()

    def _write_tests(self, colkeys, phase):
        if self.current_confdata['testfile'] is None:
            return
        self._append_matching_tests(colkeys, phase)
        if self.testcontent == {}:
            print("No testdata for TARGET")
            sys.exit(1)
        self._write_test_file()

    def _append_matching_tests(self, colkeys, phase):
        test_count = 1
        for colkey in colkeys:
            for test in self._matching_tests(colkey):
                self._append_test(test, phase, test_count)
                test_count += 1

    def _matching_tests(self, colkey):
        for test in self.current_testdata.get('targets', []):
            if colkey == '' or test['target'] == colkey:
                yield test

    def _append_test(self, test, phase, test_count):
        if self.testcontent == {}:
            self.testcontent = copy.deepcopy(self.testdict['header'])
            self.testcontent['meta']['name'] = self.current_confdata['testfile']
        item = copy.deepcopy(self.testdict['item'])
        item['test_title'] = "%d-%d" % (self.currid, test_count)
        item['ruleid'] = self.currid
        item['test_id'] = test_count
        item['desc'] = "Test case for rule %d, #%d" % (self.currid, test_count)
        item['stages'][0]['description'] = "Send request"
        self._configure_test_input(item, test, phase)
        self._configure_test_output(item, test)
        self.testcontent['tests'].append(item)

    def _configure_test_input(self, item, test, phase):
        request_input = item['stages'][0]['input']
        request_input['method'] = self.current_confdata['phase_methods'][phase].upper()
        method = self.current_testdata['phase_methods'][phase].lower()
        self._set_request_data(request_input, test['test']['data'], method)
        self._apply_custom_test_input(request_input, test['test'])

    def _set_request_data(self, request_input, data, method):
        if method == "post":
            self._set_post_data(request_input, data)
            request_input['uri'] = "/post"
        if method == "get" and isinstance(data, dict):
            key, value = next(iter(data.items()))
            request_input['uri'] = "/?%s=%s" % (key, value)

    def _set_post_data(self, request_input, data):
        if isinstance(data, dict):
            key, value = next(iter(data.items()))
            request_input['data'] = "%s=%s" % (key, value)
        elif isinstance(data, str):
            request_input['data'] = "%s" % (data)

    def _apply_custom_test_input(self, request_input, test_data):
        if 'input' not in test_data:
            return
        custom_input = test_data['input']
        for header in custom_input.get('headers', []):
            request_input['headers'][header['name']] = header['value']
        for field in ('encoded_request', 'uri'):
            if field in custom_input:
                request_input[field] = custom_input[field]

    def _configure_test_output(self, item, test):
        output = item['stages'][0]['output']
        if 'output' not in test['test']:
            output['log']['expect_ids'].append(self.currid)
            return
        item['stages'][0]['output'] = test['test']['output']
        self._update_output_rule_ids(item['stages'][0]['output'])

    def _update_output_rule_ids(self, output):
        if 'log' not in output:
            return
        log = output['log']
        if 'expect_ids' in log:
            log['expect_ids'] = [self.currid]
        if 'no_expect_ids' in log:
            log['no_expect_ids'] = [self.currid]

    def _write_test_file(self):
        filename = "%d_" % (self.currid) + self.current_confdata['testfile'].replace(".yaml", "") + ".yaml"
        self.writetest(filename, self.testcontent)
        print("testfile written: %s" % (filename))
        self.testcontent = {}

    def _advance_rule_id(self, directives_defined, after_each_template, last_id):
        if directives_defined or after_each_template is not None:
            self.currid = last_id
        self.currid += 1

    def _write_after_template(self, template):
        if template is None:
            return
        after = template.ruleid_substitute(
            increment_id_after_sub=True,
            **{'CURRID': self.currid},
        ) + "\n"
        self.content += after
        self.currid = template.get_last_id()

    def parseactions(self, action):
        """From a list of actions as str, return a single str for inclusion in the template"""
        res = ""
        for i in range(len(action)):
            if i == len(action) - 1:
                res += action[i]
            else:
                res += action[i] + ",\\\n" + self.indent

        return res

    def parsedirectives(self, directive):
        """From a list of directives as str, return a single str for inclusion in the template"""
        res = ""
        for i in range(len(directive)):
            if i == len(directive) - 1:
                res += directive[i]
            else:
                res += directive[i] + "\n"

        return res

    def genobject(self, o):
        """generate an object, eg. 'secrule' or 'secaction'"""
        obj = ""
        objects = ""
        if o['object'].lower() == "secaction":
            obj += "SecAction \\\n"

        if o['object'].lower() == "secrule":
            obj += "SecRule %s \"%s\"\\\n" % (o['target'], o['operator'])

        if o['object'].lower() in ["secaction", "secrule"]:
            self.indentdepth += 1
            if 'actions' in o:
                objects = self.buildactions(o['actions'])
            self.indentdepth -= 1
        self.content += obj + objects + "\n\n"

    def writeconf(self, obj):
        """write the generated content"""
        try:
            output_path = path_within(self.expdir, self.current_confdata['rulefile'], "rulefile")
            with open(output_path, 'w') as fp:
                fp.write(obj)
        except Exception as e:
            print(", ".join(e.args))
            sys.exit(1)

    def writetest(self, fname, testobj):
        """write the generated test"""
        testcontent = yaml.dump(
            testobj,
            indent=2,
            sort_keys = False,
            default_flow_style = False,
            explicit_start = True
        )
        try:
            output_path = path_within(self.testdir, fname, "testfile")
            with open(output_path, 'w') as fp:
                fp.write(testcontent)
        except Exception as e:
            print(", ".join(e.args))
            sys.exit(1)

    def buildactions(self, oa):
        """build the actionlist"""
        objacts = []
        aidx = 0
        for a in oa:
            if aidx == 0:
                quote = "\""
            else:
                quote = ""
            if oa[a] is not None:
                if isinstance(oa[a], int):
                    objacts.append("%s%s%s:%d" % (self.indentdepth*self.indent, quote, a, oa[a]))
                elif isinstance(oa[a], str):
                    objacts.append("%s%s%s:%s" % (self.indentdepth*self.indent, quote, a, oa[a]))
            else:
                objacts.append("%s%s%s" % (self.indentdepth*self.indent, quote, a))
            aidx += 1
        objacts = ",\\\n".join(objacts)
        return objacts + "\""


class RuleGeneratorTemplate(string.Template):
    pattern = r'''
    \${(?:
       (?P<escaped>\$) |               
       (?P<named>[^ \n\t$,'"]*)\}\$ |    
       \b\B(?P<braced>) |             
       (?P<invalid>)                  
    )
    '''

    def __init__(self, template):
        super().__init__(template)
        self.last_id = 0

    def get_last_id(self):
        return self.last_id

    def ruleid_substitute(self, increment_id_after_sub=False, **kwargs):
        """Increments CURRID before or after each substitution for macros"""
        def incrementing_substitution(match):
            var_name = match.group('named')
            if var_name == 'CURRID':
                if increment_id_after_sub:
                    kwargs['CURRID'] += 1
                    self.last_id = kwargs['CURRID']
                    return str(kwargs['CURRID'] - 1)
                else:  # increment before substitution
                    kwargs['CURRID'] += 1
                    self.last_id = kwargs['CURRID']
                    return str(kwargs['CURRID'])
            elif var_name in kwargs:
                return str(kwargs[var_name])
            else:
                return match.group(0)

        return re.compile(self.pattern).sub(incrementing_substitution, self.template)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MRTS rule generate tool")
    parser.add_argument("-r", "--rulesdef", metavar='/path/to/mrts/*.yaml', type=str,
                            nargs='*', help='Directory path to MRTS rules definition', required=True,
                            action="append")
    parser.add_argument("-e", "--expdir", metavar='/path/to/mrts/rules/', type=str,
                            help='Directory path to generated MRTS rules', required=True)
    parser.add_argument("-t", "--testdir", metavar='/path/to/mrts/tests/', type=str,
                            help='Directory path to generated MRTS tests', required=True)
    args = parser.parse_args()

    mrtspath = []
    for l in args.rulesdef:
        mrtspath += l

    retval = 0
    try:
        flist = mrtspath
        flist.sort()
    except:
        print("Can't open files in given path!")
        sys.exit(1)

    if len(flist) == 0:
        print("List of files is empty!")
        sys.exit(1)

    try:
        gen = RuleGenerator(flist, args.expdir, args.testdir)
    except ValueError as error:
        parser.error(str(error))


    sys.exit(retval)
