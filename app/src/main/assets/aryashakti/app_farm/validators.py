from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail

class AddFarmDataValidator(serializers.Serializer):
    crop_id = serializers.IntegerField(required=True)
    mobile_number = serializers.IntegerField(required=True)
    name = serializers.CharField(min_length=2, max_length=100, required=True)
    country_id = serializers.IntegerField(required=True)

    # Removing the validation from lat and long (for time being).
    """
    lat = serializers.FloatField(required=False, allow_null=True)
    long = serializers.FloatField(required=False, allow_null=True)

    def custom_lat_long_validation(self, value):
        if value == None:
            return ErrorDetail(string='This field is required.', code='required')
        else:
            int_part = str(value).split('.')[0]
            if len(int_part) > 10:
                return ErrorDetail(string='Ensure that there are no more than 10 digits in total.', code='max_digits')
        return None

    def validate(self, data):
        if data['is_location']:
            errors = {}
            lat_result = self.custom_lat_long_validation(data.get('lat'))
            if lat_result:
                errors['lat'] = lat_result

            long_result = self.custom_lat_long_validation(data.get('long'))
            if long_result:
                errors['long'] = long_result

            raise serializers.ValidationError(errors)
        return data
    """
