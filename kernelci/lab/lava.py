# Copyright (C) 2019 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
#
# Copyright (C) 2019 Linaro Limited
# Author: Dan Rue <dan.rue@linaro.org>
#
# This module is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

from jinja2 import Environment, FileSystemLoader
import urllib.parse
import requests
import os
from kernelci.lab import LabAPI


class LAVA(LabAPI):
    """Interface to a LAVA lab

    This implementation of kernelci.lab.LabAPI is to communicate with LAVA
    labs.  It can retrieve some information such as the list of devices and
    their online status, generate and submit jobs with callback parameters.
    One special thing it can deal with is job priorities, which is only
    available in kernelci.config.lab.lab_LAVA objects.
    """

    def connect(self, user=None, token=None):
        super().connect(user, token)
        self._lava_token = token

    def _rest_query(self, endpoint, ordering, limit=50):
        base_url = urllib.parse.urljoin(
            self.config.url, f'api/v0.2/{endpoint}/'
        )
        headers = {'Authorization': f"Token {self._lava_token}"}
        offset = 0
        results = []
        while True:
            query = urllib.parse.urlencode(
                {'offset': offset, 'limit': limit, 'ordering': ordering}
            )
            url = '?'.join([base_url, query])
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            results.extend(data['results'])
            total = int(data['count'])
            if len(results) < total:
                offset += limit
            else:
                break
        return results

    def _get_devices(self):
        devices = self._rest_query('devices', 'hostname')
        all_devices = [
            tuple(dev[key] for key in ['hostname', 'device_type', 'health'])
            for dev in devices
        ]

        aliases = self._rest_query('aliases', 'name')
        all_aliases = {
            alias['name']: alias['device_type']
            for alias in aliases
        }

        device_types = {}
        for device in all_devices:
            name, device_type, health = device
            device_list = device_types.setdefault(device_type, list())
            device_list.append({
                'name': name,
                'online': health == "Good",
            })
        online_status = {
            device_type: any(device['online'] for device in devices)
            for device_type, devices in device_types.items()
        }

        return {
            'online_status': online_status,
            'aliases': all_aliases,
        }

    def _add_callback_params(self, params, opts):
        callback_id = opts.get('id')
        if not callback_id:
            return
        callback_type = opts.get('type')
        if callback_type == 'kernelci':
            lava_cb = 'boot' if params['plan'] == 'boot' else 'test'
            # ToDo: consolidate this to just have to pass the callback_url
            params['callback_name'] = '/'.join(['lava', lava_cb])
        params.update({
            'callback': callback_id,
            'callback_url': opts['url'],
            'callback_dataset': opts['dataset'],
            'callback_type': callback_type,
        })

    def _alias_device_type(self, device_type):
        aliases = self.devices.get('aliases', dict())
        return aliases.get(device_type, device_type)

    def device_type_online(self, device_type_config):
        device_type = self._alias_device_type(device_type_config.base_name)
        online_status = self.devices.get('online_status', dict())
        return online_status.get(device_type, False)

    def job_file_name(self, params):
        return '.'.join([params['name'], 'yaml'])

    def generate(self, params, target, plan, callback_opts):
        short_template_file = plan.get_template_path(target.boot_method)
        template_file = os.path.join('config/lava', short_template_file)
        if not os.path.exists(template_file):
            print("Template not found: {}".format(template_file))
            return None
        base_name = params['base_device_type']
        params.update({
            'template_file': template_file,
            'priority': self.config.priority,
            'lab_name': self.config.name,
            'base_device_type': self._alias_device_type(base_name),
        })
        self._add_callback_params(params, callback_opts)
        jinja2_env = Environment(loader=FileSystemLoader('config/lava'),
                                 extensions=["jinja2.ext.do"])
        template = jinja2_env.get_template(short_template_file)
        data = template.render(params)
        return data

    def submit(self, job):
        return self._server.scheduler.submit_job(job)


def get_api(lab):
    """Get a LAVA lab API object"""
    return LAVA(lab)
