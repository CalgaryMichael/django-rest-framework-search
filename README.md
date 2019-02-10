# django-rest-framework-search
An improved API for Django Rest Framework SearchFilters
* Builtin ability to validate the search criteria for a field
  * This will ensure that the only fields that are searched on are the ones that pass their validation
* Able to filter a search string by specifying the field name
  * Example: `email: miles.davis@jazz.com`
* Allows for multiple filtered fields
  * Example: `fname: Miles, lname: Davis`
  * _Note_: see _Limitations_ section for more info

## Examples
```python
from drf_search import filters, fields
class UserSearchFilter(filters.BaseSearchFilter):
    id = fields.IntegerSearchField("id", validators=[lambda x: uuid.UUID(x)] default=True)
    email = fields.EmailSearchField("email", partial=True, default=True)
    first_name = fields.StringSearchField("fname")
    last_name = fields.StringSearchField("lname")
```

## Limitations
* Currently the filtering logic only supports the _AND_ operator to combine multiple query values
