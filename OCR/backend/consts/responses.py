from typing import Any, Dict, Union

from rest_framework import status
from rest_framework.response import Response

response_type = Dict[str, Union[str, int]]


class Responses:
    class GENERAL:
        OK = {'code': 'success', 'status': status.HTTP_200_OK, 'message': 'success'}
        NOT_FOUND = {
            'code': 'not_found',
            'status': status.HTTP_404_NOT_FOUND,
            'message': 'داده مورد نظر یافت نشد',
        }
        WRONG_INPUTS = {
            'code': 'wrong_inputs',
            'status': status.HTTP_400_BAD_REQUEST,
            'message': 'داده های ورودی صحیح نمی باشد',
        }
        FORBIDDEN = {
            'code': 'forbidden',
            'status': status.HTTP_400_BAD_REQUEST,
            'message': 'عملیات مجاز نمی باشد',
        }
        SERVER_ERROR = {
            'code': 'server_error',
            'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'message': 'خطای سرور، لطفا دوباره امتحان کنید.',
        }
        DATA_NOT_FOUND = {
            'code': 'data_not_found',
            'status': status.HTTP_404_NOT_FOUND,
            'message': 'اطلاعات یافت نشد.',
        }
        USER_NOT_FOUND = {
            'code': 'user_not_found',
            'status': status.HTTP_404_NOT_FOUND,
            'message': 'کاربر یافت نشد.',
        }
        GATEWAY_ERROR = {
            'code': 'gateway_error',
            'status': status.HTTP_400_BAD_REQUEST,
            'message': 'خطای سرویس دهنده. لطفا دوباره امتحان کنید',
        }

    class ACCOUNT_GENERAL:
        INVALID_PASSWORD = {
            'code': 'invalid_password',
            'status': status.HTTP_400_BAD_REQUEST,
            'message': 'رمز عبور اشتباه است',
        }
        DISABLED = {
            'code': 'DISABLED',
            'status': status.HTTP_403_FORBIDDEN,
            'message': 'دسترسی این اکانت غیرفعال است',
        }

    class FILE:
        FILE_TOO_LARGE = {
            'code': 'file_too_large',
            'status': status.HTTP_400_BAD_REQUEST,
            'message': 'اندازه فایل بزرگتر از حد مجاز است',
        }
        INVALID_FILE_TYPE = {
            'code': 'invalie_file_type',
            'status': status.HTTP_400_BAD_REQUEST,
            'message': 'امکان ارسال این نوع فایل وجود ندارد',
        }

    @classmethod
    def get_response(cls, res_type: response_type, data: Any = None) -> Response:
        response_data = {'state': res_type['code'], 'message': res_type['message']}

        if data is not None:
            response_data['data'] = data

        return Response(response_data, status=res_type['status'])


# Sample usage:
# return Responses.get_response(Responses.General.USER_NOT_FOUND)
