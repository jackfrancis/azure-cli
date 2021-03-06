# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (LiveTest, ResourceGroupPreparer, StorageAccountPreparer)
from .storage_test_util import StorageScenarioMixin


class StorageBlobCopyTests(StorageScenarioMixin, LiveTest):
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='source_account')
    @StorageAccountPreparer(parameter_name='target_account')
    def test_storage_blob_copy_with_sas_and_snapshot(self, resource_group, source_account, target_account):
        source_file = self.create_temp_file(16, full_random=True)
        source_account_info = self.get_account_info(resource_group, source_account)
        target_account_info = self.get_account_info(resource_group, target_account)

        with open(source_file, 'rb') as f:
            expect_content = f.read()

        source_container = self.create_container(source_account_info)
        target_container = self.create_container(target_account_info)

        self.storage_cmd('storage blob upload -c {} -f {} -n src', source_account_info,
                         source_container, source_file)

        snapshot = self.storage_cmd('storage blob snapshot -c {} -n src', source_account_info,
                                    source_container).get_output_in_json()['snapshot']

        source_file = self.create_temp_file(24, full_random=True)
        self.storage_cmd('storage blob upload -c {} -f {} -n src', source_account_info,
                         source_container, source_file)

        from datetime import datetime, timedelta
        start = datetime.utcnow().strftime('%Y-%m-%dT%H:%MZ')
        expiry = (datetime.utcnow() + timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%MZ')
        sas = self.storage_cmd('storage blob generate-sas -c {} -n src --permissions r --start {}'
                               ' --expiry {}', source_account_info, source_container, start,
                               expiry).output.strip()

        self.storage_cmd('storage blob copy start -b dst -c {} --source-blob src --source-sas {} '
                         '--source-account-name {} --source-container {} --source-snapshot {}',
                         target_account_info, target_container, sas, source_account,
                         source_container, snapshot)

        target_file = self.create_temp_file(1)
        self.storage_cmd('storage blob download -c {} -n dst -f {}', target_account_info,
                         target_container, target_file)

        with open(target_file, 'rb') as f:
            actual_content = f.read()

        self.assertEqual(expect_content, actual_content)
