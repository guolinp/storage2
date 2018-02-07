#!/usr/bin/python

err_success = 0
err_invalid_argument = 1024
err_out_of_range = 1025
err_read_data_fail = 1025
err_write_data_fail = 1027

def is_success(err):
    return err == err_success
