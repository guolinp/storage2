#!/usr/bin/python

# Error code defines

err_success = 0
err_invalid_argument = 1024
err_out_of_range = 1025
err_read_data_fail = 1025
err_write_data_fail = 1027
err_not_implement = 1028
err_disk_not_enough = 1029
err_disk_too_more = 1030
err_disk_be_bad = 1031

# Error helper functions


def is_success(err):
    return err == err_success


# Assert

def assert_success(err):
    assert(is_success(err))


def assert_failed(err):
    assert(not is_success(err))


def assert_true(condition):
    assert(condition)


def assert_false(condition):
    assert(not (condition))


def assert_is_instance(instance, class_or_type):
    assert(isinstance(instance, class_or_type))


def assert_is_not_instance(instance, class_or_type):
    assert(not isinstance(instance, class_or_type))


def assert_is_subclass(child, parent):
    assert(issubclass(child, parent))


def assert_is_not_subclass(child, parent):
    assert(not issubclass(child, parent))


def assert_is_none(instance):
    assert(instance is None)


def assert_is_not_none(instance):
    assert(instance is not None)


def assert_is_list(instance):
    assert(type(instance) == list)


def assert_is_dict(instance):
    assert(type(instance) == dict)


def assert_is_tuple(instance):
    assert(type(instance) == tuple)


def assert_is_int(instance):
    assert(type(instance) == int)


def assert_is_str(instance):
    assert(type(instance) == str)


def assert_is_bool(instance):
    assert(type(instance) == bool)


def assert_is_float(instance):
    assert(type(instance) == float)


def assert_is_same(instance1, instance2):
    assert(instance1 is instance2)


def assert_is_not_same(instance1, instance2):
    assert(instance1 is not instance2)


def assert_int_equal(instance1, instance1):
    assert_is_int(instance1)
    assert_is_int(instance2)
    assert(instance1 == instance2)


def assert_float_equal(instance1, instance1):
    assert_is_float(instance1)
    assert_is_float(instance2)
    assert(instance1 == instance2)


def assert_str_equal(instance1, instance2):
    assert_is_str(instance1)
    assert_is_str(instance2)
    assert(instance1 == instance2)


def assert_bool_equal(instance1, instance2):
    assert_is_bool(instance1)
    assert_is_bool(instance2)
    assert(instance1 == instance2)

# Exceptions


class StorgeError(Exception):

    def __init__(self, value='A storage error'):
        self._value = value

    def __str__(self):
        return 'Error value: %s' % self._value


class InvalidArgumentError(StorgeError):
    pass


class DeviceNotFoundError(StorgeError):
    pass


class DeviceNotAvailableError(StorgeError):
    pass


class DeviceAccessError(StorgeError):
    pass


class DeviceNoEnoughSpaceError(StorgeError):
    pass


class FunctionalNotImplementError(StorgeError):
    pass


class RaidBuildError(StorgeError):
    pass


class BadSuperBlockError(StorgeError):
    pass
