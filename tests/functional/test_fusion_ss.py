# -*- coding: utf-8 -*-

# (c) 2023, Andrej Pajtas (apajtas@purestorage.com)
# GNU General Public License v3.0+ (see COPYING.GPLv3 or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import MagicMock, patch

import fusion as purefusion
import pytest
from ansible.module_utils import basic
from ansible_collections.purestorage.fusion.plugins.module_utils.errors import (
    OperationException,
)
from ansible_collections.purestorage.fusion.plugins.modules import fusion_ss
from ansible_collections.purestorage.fusion.tests.functional.utils import (
    AnsibleExitJson,
    AnsibleFailJson,
    FailedOperationMock,
    OperationMock,
    SuccessfulOperationMock,
    exit_json,
    fail_json,
    set_module_args,
)
from urllib3.exceptions import HTTPError

# GLOBAL MOCKS
fusion_ss.setup_fusion = MagicMock(return_value=purefusion.api_client.ApiClient())
purefusion.api_client.ApiClient.call_api = MagicMock(
    side_effect=Exception("API call not mocked!")
)
basic.AnsibleModule.exit_json = exit_json
basic.AnsibleModule.fail_json = fail_json


@patch("fusion.OperationsApi")
@patch("fusion.StorageServicesApi")
@pytest.mark.parametrize(
    "module_args",
    [
        # required parameter 'name` is missing
        {
            "state": "present",
            "display_name": "Storage Service 1",
            "hardware_types": ["flash-array-x"],
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # unknown parameter 'extra' is provided
        {
            "state": "present",
            "name": "ss1",
            "display_name": "Storage Service 1",
            "hardware_types": ["flash-array-x"],
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
            "extra": "value",
        },
        # parameter 'state` has incorrect value
        {
            "state": "cool",
            "name": "ss1",
            "display_name": "Storage Service 1",
            "hardware_types": ["flash-array-x"],
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
        # parameter 'hardware_types` has incorrect value
        {
            "state": "present",
            "name": "ss1",
            "display_name": "Storage Service 1",
            "hardware_types": ["hdd-array-x"],
            "issuer_id": "ABCD1234",
            "private_key_file": "private-key.pem",
        },
    ],
)
def test_module_fails_on_wrong_parameters(m_ss_api, m_op_api, module_args):
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_service = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_service = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_service = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_service = MagicMock(return_value=OperationMock(3))

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj
    m_ss_api.return_value = api_obj

    # run module
    with pytest.raises(AnsibleFailJson):
        fusion_ss.main()

    # check api was not called at all
    api_obj.get_storage_service.assert_not_called()
    api_obj.create_storage_service.assert_not_called()
    api_obj.update_storage_service.assert_not_called()
    api_obj.delete_storage_service.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageServicesApi")
def test_ss_create(m_ss_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "ss1",
        "display_name": "Storage Service 1",
        "hardware_types": ["flash-array-x"],
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_service = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_service = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_service = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_service = MagicMock(return_value=OperationMock(3))
    m_ss_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_ss.main()

    assert exc.value.changed

    # check api was called correctly
    api_obj.get_storage_service.assert_called_once_with(
        storage_service_name=module_args["name"]
    )
    api_obj.create_storage_service.assert_called_once_with(
        purefusion.StorageServicePost(
            name=module_args["name"],
            display_name=module_args["display_name"],
            hardware_types=module_args["hardware_types"],
        )
    )
    api_obj.update_storage_service.assert_not_called()
    api_obj.delete_storage_service.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.StorageServicesApi")
def test_ss_create_without_display_name(m_ss_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "ss1",
        "hardware_types": ["flash-array-x"],
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_service = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_service = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_service = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_service = MagicMock(return_value=OperationMock(3))
    m_ss_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_ss.main()

    assert exc.value.changed

    # check api was called correctly
    api_obj.get_storage_service.assert_called_once_with(
        storage_service_name=module_args["name"]
    )
    api_obj.create_storage_service.assert_called_once_with(
        purefusion.StorageServicePost(
            name=module_args["name"],
            display_name=module_args["name"],
            hardware_types=module_args["hardware_types"],
        )
    )
    api_obj.update_storage_service.assert_not_called()
    api_obj.delete_storage_service.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.StorageServicesApi")
def test_array_create_without_hardware_type(m_ss_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "ss1",
        "display_name": "Storage Service 1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_service = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_service = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_service = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_service = MagicMock(return_value=OperationMock(3))

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj
    m_ss_api.return_value = api_obj

    # run module
    with pytest.raises(AnsibleFailJson):
        fusion_ss.main()

    # check api was not called at all
    api_obj.get_storage_service.assert_called_once_with(
        storage_service_name=module_args["name"]
    )
    api_obj.create_storage_service.assert_not_called()
    api_obj.update_storage_service.assert_not_called()
    api_obj.delete_storage_service.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageServicesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_ss_create_exception(m_ss_api, m_op_api, exec_original, exec_catch):
    module_args = {
        "state": "present",
        "name": "ss1",
        "display_name": "Storage Service 1",
        "hardware_types": ["flash-array-x"],
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_service = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_service = MagicMock(side_effect=exec_original)
    api_obj.update_storage_service = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_service = MagicMock(return_value=OperationMock(3))
    m_ss_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_ss.main()

    # check api was called correctly
    api_obj.get_storage_service.assert_called_once_with(
        storage_service_name=module_args["name"]
    )
    api_obj.create_storage_service.assert_called_once_with(
        purefusion.StorageServicePost(
            name=module_args["name"],
            display_name=module_args["display_name"],
            hardware_types=module_args["hardware_types"],
        )
    )
    api_obj.update_storage_service.assert_not_called()
    api_obj.delete_storage_service.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageServicesApi")
def test_ss_create_op_fails(m_ss_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "ss1",
        "display_name": "Storage Service 1",
        "hardware_types": ["flash-array-x"],
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_service = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_service = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_service = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_service = MagicMock(return_value=OperationMock(3))
    m_ss_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(OperationException):
        fusion_ss.main()

    # check api was called correctly
    api_obj.get_storage_service.assert_called_once_with(
        storage_service_name=module_args["name"]
    )
    api_obj.create_storage_service.assert_called_once_with(
        purefusion.StorageServicePost(
            name=module_args["name"],
            display_name=module_args["display_name"],
            hardware_types=module_args["hardware_types"],
        )
    )
    api_obj.update_storage_service.assert_not_called()
    api_obj.delete_storage_service.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.StorageServicesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_ss_create_op_exception(m_ss_api, m_op_api, exec_original, exec_catch):
    module_args = {
        "state": "present",
        "name": "ss1",
        "display_name": "Storage Service 1",
        "hardware_types": ["flash-array-x"],
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_service = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_service = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_service = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_service = MagicMock(return_value=OperationMock(3))
    m_ss_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(side_effect=exec_original)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_ss.main()

    # check api was called correctly
    api_obj.get_storage_service.assert_called_once_with(
        storage_service_name=module_args["name"]
    )
    api_obj.create_storage_service.assert_called_once_with(
        purefusion.StorageServicePost(
            name=module_args["name"],
            display_name=module_args["display_name"],
            hardware_types=module_args["hardware_types"],
        )
    )
    api_obj.update_storage_service.assert_not_called()
    api_obj.delete_storage_service.assert_not_called()
    op_obj.get_operation.assert_called_once_with(1)


@patch("fusion.OperationsApi")
@patch("fusion.StorageServicesApi")
def test_ss_update(m_ss_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "ss1",
        "display_name": "Storage Service 1",
        "hardware_types": ["flash-array-x"],
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_ss = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "display_name": None,
        "hardware_types": ["flash-array-c"],  # is different but shouldn't be patched!
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_service = MagicMock(
        return_value=purefusion.StorageService(**current_ss)
    )
    api_obj.create_storage_service = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_service = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_service = MagicMock(return_value=OperationMock(3))
    m_ss_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_ss.main()

    assert exc.value.changed

    # check api was called correctly
    api_obj.get_storage_service.assert_called_once_with(
        storage_service_name=module_args["name"]
    )
    api_obj.create_storage_service.assert_not_called()
    api_obj.update_storage_service.assert_called_once_with(
        purefusion.StorageServicePatch(
            display_name=purefusion.NullableString(module_args["display_name"])
        ),
        storage_service_name=module_args["name"],
    )
    api_obj.delete_storage_service.assert_not_called()
    op_obj.get_operation.assert_called_once_with(2)


@patch("fusion.OperationsApi")
@patch("fusion.StorageServicesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_ss_update_exception(m_ss_api, m_op_api, exec_original, exec_catch):
    module_args = {
        "state": "present",
        "name": "ss1",
        "display_name": "Storage Service 1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_ss = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "display_name": None,
        "hardware_types": ["flash-array-x"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_service = MagicMock(
        return_value=purefusion.StorageService(**current_ss)
    )
    api_obj.create_storage_service = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_service = MagicMock(side_effect=exec_original)
    api_obj.delete_storage_service = MagicMock(return_value=OperationMock(3))
    m_ss_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_ss.main()

    # check api was called correctly
    api_obj.get_storage_service.assert_called_once_with(
        storage_service_name=module_args["name"]
    )
    api_obj.create_storage_service.assert_not_called()
    api_obj.update_storage_service.assert_called_once_with(
        purefusion.StorageServicePatch(
            display_name=purefusion.NullableString(module_args["display_name"])
        ),
        storage_service_name=module_args["name"],
    )
    api_obj.delete_storage_service.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageServicesApi")
def test_ss_update_op_fails(m_ss_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "ss1",
        "display_name": "Storage Service 1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_ss = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "display_name": None,
        "hardware_types": ["flash-array-x"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_service = MagicMock(
        return_value=purefusion.StorageService(**current_ss)
    )
    api_obj.create_storage_service = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_service = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_service = MagicMock(return_value=OperationMock(3))
    m_ss_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(OperationException):
        fusion_ss.main()

    # check api was called correctly
    api_obj.get_storage_service.assert_called_once_with(
        storage_service_name=module_args["name"]
    )
    api_obj.create_storage_service.assert_not_called()
    api_obj.update_storage_service.assert_called_once_with(
        purefusion.StorageServicePatch(
            display_name=purefusion.NullableString(module_args["display_name"])
        ),
        storage_service_name=module_args["name"],
    )
    api_obj.delete_storage_service.assert_not_called()
    op_obj.get_operation.assert_called_once_with(2)


@patch("fusion.OperationsApi")
@patch("fusion.StorageServicesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_ss_update_op_exception(m_ss_api, m_op_api, exec_original, exec_catch):
    module_args = {
        "state": "present",
        "name": "ss1",
        "display_name": "Storage Service 1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_ss = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "display_name": None,
        "hardware_types": ["flash-array-x"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_service = MagicMock(
        return_value=purefusion.StorageService(**current_ss)
    )
    api_obj.create_storage_service = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_service = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_service = MagicMock(return_value=OperationMock(3))
    m_ss_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(side_effect=exec_original)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_ss.main()

    # check api was called correctly
    api_obj.get_storage_service.assert_called_once_with(
        storage_service_name=module_args["name"]
    )
    api_obj.create_storage_service.assert_not_called()
    api_obj.update_storage_service.assert_called_once_with(
        purefusion.StorageServicePatch(
            display_name=purefusion.NullableString(module_args["display_name"])
        ),
        storage_service_name=module_args["name"],
    )
    api_obj.delete_storage_service.assert_not_called()
    op_obj.get_operation.assert_called_once_with(2)


@patch("fusion.OperationsApi")
@patch("fusion.StorageServicesApi")
def test_ss_present_not_changed(m_ss_api, m_op_api):
    module_args = {
        "state": "present",
        "name": "ss1",
        "display_name": "Storage Service 1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_ss = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "display_name": module_args["display_name"],
        "hardware_types": ["flash-array-x"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_service = MagicMock(
        return_value=purefusion.StorageService(**current_ss)
    )
    api_obj.create_storage_service = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_service = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_service = MagicMock(return_value=OperationMock(3))
    m_ss_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_ss.main()

    assert not exc.value.changed

    # check api was called correctly
    api_obj.get_storage_service.assert_called_once_with(
        storage_service_name=module_args["name"]
    )
    api_obj.create_storage_service.assert_not_called()
    api_obj.update_storage_service.assert_not_called()
    api_obj.delete_storage_service.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageServicesApi")
def test_ss_absent_not_changed(m_ss_api, m_op_api):
    module_args = {
        "state": "absent",
        "name": "ss1",
        "display_name": "Storage Service 1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_service = MagicMock(side_effect=purefusion.rest.ApiException)
    api_obj.create_storage_service = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_service = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_service = MagicMock(return_value=OperationMock(3))
    m_ss_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_ss.main()

    assert not exc.value.changed

    # check api was called correctly
    api_obj.get_storage_service.assert_called_once_with(
        storage_service_name=module_args["name"]
    )
    api_obj.create_storage_service.assert_not_called()
    api_obj.update_storage_service.assert_not_called()
    api_obj.delete_storage_service.assert_not_called()
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageServicesApi")
def test_ss_delete(m_ss_api, m_op_api):
    module_args = {
        "state": "absent",
        "name": "ss1",
        "display_name": "Storage Service 1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_ss = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "display_name": "different",  # display_name doesn't match but UPDATE shouldn't be called
        "hardware_types": ["flash-array-x"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_service = MagicMock(
        return_value=purefusion.StorageService(**current_ss)
    )
    api_obj.create_storage_service = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_service = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_service = MagicMock(return_value=OperationMock(3))
    m_ss_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=SuccessfulOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(AnsibleExitJson) as exc:
        fusion_ss.main()

    assert exc.value.changed

    # check api was called correctly
    api_obj.get_storage_service.assert_called_once_with(
        storage_service_name=module_args["name"]
    )
    api_obj.create_storage_service.assert_not_called()
    api_obj.update_storage_service.assert_not_called()
    api_obj.delete_storage_service.assert_called_once_with(
        storage_service_name=module_args["name"]
    )
    op_obj.get_operation.assert_called_once_with(3)


@patch("fusion.OperationsApi")
@patch("fusion.StorageServicesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, HTTPError),
    ],
)
def test_ss_delete_exception(m_ss_api, m_op_api, exec_original, exec_catch):
    module_args = {
        "state": "absent",
        "name": "ss1",
        "display_name": "Storage Service 1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_ss = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "display_name": "different",  # display_name doesn't match but UPDATE shouldn't be called
        "hardware_types": ["flash-array-x"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_service = MagicMock(
        return_value=purefusion.StorageService(**current_ss)
    )
    api_obj.create_storage_service = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_service = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_service = MagicMock(side_effect=exec_original)
    m_ss_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_ss.main()

    # check api was called correctly
    api_obj.get_storage_service.assert_called_once_with(
        storage_service_name=module_args["name"]
    )
    api_obj.create_storage_service.assert_not_called()
    api_obj.update_storage_service.assert_not_called()
    api_obj.delete_storage_service.assert_called_once_with(
        storage_service_name=module_args["name"]
    )
    op_obj.get_operation.assert_not_called()


@patch("fusion.OperationsApi")
@patch("fusion.StorageServicesApi")
def test_ss_delete_op_fails(m_ss_api, m_op_api):
    module_args = {
        "state": "absent",
        "name": "ss1",
        "display_name": "Storage Service 1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_ss = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "display_name": "different",  # display_name doesn't match but UPDATE shouldn't be called
        "hardware_types": ["flash-array-x"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_service = MagicMock(
        return_value=purefusion.StorageService(**current_ss)
    )
    api_obj.create_storage_service = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_service = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_service = MagicMock(return_value=OperationMock(3))
    m_ss_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(return_value=FailedOperationMock)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(OperationException):
        fusion_ss.main()

    # check api was called correctly
    api_obj.get_storage_service.assert_called_once_with(
        storage_service_name=module_args["name"]
    )
    api_obj.create_storage_service.assert_not_called()
    api_obj.update_storage_service.assert_not_called()
    api_obj.delete_storage_service.assert_called_once_with(
        storage_service_name=module_args["name"]
    )
    op_obj.get_operation.assert_called_once_with(3)


@patch("fusion.OperationsApi")
@patch("fusion.StorageServicesApi")
@pytest.mark.parametrize(
    "exec_original,exec_catch",
    [
        (purefusion.rest.ApiException, purefusion.rest.ApiException),
        (HTTPError, OperationException),
    ],
)
def test_ss_delete_op_exception(m_ss_api, m_op_api, exec_original, exec_catch):
    module_args = {
        "state": "absent",
        "name": "ss1",
        "display_name": "Storage Service 1",
        "issuer_id": "ABCD1234",
        "private_key_file": "private-key.pem",
    }
    current_ss = {
        "id": 1,
        "self_link": "self_link_value",
        "name": module_args["name"],  # name must match
        "display_name": "different",  # display_name doesn't match but UPDATE shouldn't be called
        "hardware_types": ["flash-array-x"],
    }
    set_module_args(module_args)

    # mock api responses
    api_obj = MagicMock()
    api_obj.get_storage_service = MagicMock(
        return_value=purefusion.StorageService(**current_ss)
    )
    api_obj.create_storage_service = MagicMock(return_value=OperationMock(1))
    api_obj.update_storage_service = MagicMock(return_value=OperationMock(2))
    api_obj.delete_storage_service = MagicMock(return_value=OperationMock(3))
    m_ss_api.return_value = api_obj

    # mock operation results
    op_obj = MagicMock()
    op_obj.get_operation = MagicMock(side_effect=exec_original)
    m_op_api.return_value = op_obj

    # run module
    with pytest.raises(exec_catch):
        fusion_ss.main()

    # check api was called correctly
    api_obj.get_storage_service.assert_called_once_with(
        storage_service_name=module_args["name"]
    )
    api_obj.create_storage_service.assert_not_called()
    api_obj.update_storage_service.assert_not_called()
    api_obj.delete_storage_service.assert_called_once_with(
        storage_service_name=module_args["name"]
    )
    op_obj.get_operation.assert_called_once_with(3)
