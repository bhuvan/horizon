# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import datetime

from django import http
from django.core.urlresolvers import reverse
from mox import IsA

from horizon import api
from horizon import test
from horizon import usage
from horizon.templatetags.sizeformat import mbformat


INDEX_URL = reverse('horizon:nova:overview:index')


class UsageViewTests(test.BaseAdminViewTests):
    def tearDown(self):
        super(UsageViewTests, self).tearDown()
        self.reset_times()  # override_times is called in the tests

    @test.create_stubs({api: ('usage_list',),
                        api.keystone: ('tenant_list',)})
    def test_usage(self):
        now = self.override_times()
        usage_obj = api.nova.Usage(self.usages.first())
        api.keystone.tenant_list(IsA(http.HttpRequest), admin=True) \
                    .AndReturn(self.tenants.list())
        api.usage_list(IsA(http.HttpRequest),
                      datetime.datetime(now.year, now.month, 1,
                                        now.hour, now.minute, now.second),
                      datetime.datetime(now.year, now.month, now.day, now.hour,
                                        now.minute, now.second)) \
                      .AndReturn([usage_obj])
        self.mox.ReplayAll()
        res = self.client.get(reverse('horizon:syspanel:overview:index'))
        self.assertTemplateUsed(res, 'syspanel/overview/usage.html')
        self.assertTrue(isinstance(res.context['usage'], usage.GlobalUsage))
        self.assertContains(res,
                            '<td class="sortable">test_tenant</td>'
                            '<td class="sortable">%s</td>'
                            '<td class="sortable">%s</td>'
                            '<td class="sortable">%s</td>'
                            '<td class="sortable">%.2f</td>'
                            '<td class="sortable">%.2f</td>' %
                            (usage_obj.vcpus,
                             usage_obj.disk_gb_hours,
                             mbformat(usage_obj.memory_mb),
                             usage_obj.vcpu_hours,
                             usage_obj.total_local_gb_usage))

    @test.create_stubs({api: ('usage_list',),
                        api.keystone: ('tenant_list',)})
    def test_usage_csv(self):
        now = self.override_times()
        usage_obj = api.nova.Usage(self.usages.first())
        api.keystone.tenant_list(IsA(http.HttpRequest), admin=True) \
                    .AndReturn(self.tenants.list())
        api.usage_list(IsA(http.HttpRequest),
                      datetime.datetime(now.year, now.month, 1,
                                        now.hour, now.minute, now.second),
                      datetime.datetime(now.year, now.month, now.day, now.hour,
                                        now.minute, now.second)) \
                      .AndReturn([usage_obj])
        self.mox.ReplayAll()
        csv_url = reverse('horizon:syspanel:overview:index') + "?format=csv"
        res = self.client.get(csv_url)
        self.assertTemplateUsed(res, 'syspanel/overview/usage.csv')
        self.assertTrue(isinstance(res.context['usage'], usage.GlobalUsage))
        self.assertContains(res, 'Tenant,VCPUs,RamMB,DiskGB,Usage(Hours)\n'
                            '%s,%s,%s,%s,%f' %
                            (usage_obj.tenant_id,
                             usage_obj.vcpus,
                             usage_obj.memory_mb,
                             usage_obj.disk_gb_hours,
                             usage_obj.vcpu_hours))
