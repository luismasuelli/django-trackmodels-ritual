from abc import ABCMeta, abstractmethod
from collections import namedtuple
from cantrips import functions
from django.utils.six import text_type, string_types, StringIO
from django.utils.text import capfirst
from django.utils.timezone import now
from django.http import HttpResponse
import datetime
import csv


TrackingReportColumn = namedtuple('TrackingReportColumn', ('header', 'fetcher'))
TrackingReportResult = namedtuple('TrackingReportResult', ('headers', 'values'))


class TrackingReport(object):
    """
    This is an abstract class to process a report for a given format, model, and period.
    Stuff must be defined like:
    1. The report key and display. It must have a meaning in the software and should be allowed to the
       user to specify it. It is specified in an instance basis.
    2. The content type. This could be defined by overriding `get_attachment_content_type` method or just
       the `content_type` member (a string).
    3. The attachment name. This MUST be defined by overriding `get_attachment_filename` method.
    4. The attachment content. This MUST be defined by overriding `get_attachment_content` method.
    5. The fields to report. This can be defined by overriding `get_list_report` method or just
       the `list_report` member (a list of strings).
    """

    list_report = []
    datetime_format = "%Y-%m-%d %H:%M:%S"
    date_format = "%Y-%m-%d"
    time_format = "%H:%M:%S"

    __metaclass__ = ABCMeta
    content_type = None

    def __init__(self, key, text):
        """
        Telling a key and a value is useful to let the report be picked
        :param key: This string value must be unique across different reports in the same admin.
        :param text: This string (or locale lazy resolver) is the display text for the option.
        """

        self._key = key
        self._text = text

    def _serialize_value(self, value):
        """
        Serialize values like date and time. Respect other values:
        :return:
        """

        if isinstance(value, datetime.datetime):
            return value.strftime(self.datetime_format)
        elif isinstance(value, datetime.date):
            return value.strftime(self.date_format)
        elif isinstance(value, datetime.time):
            return value.strftime(self.time_format)
        return text_type(value)

    def _cell_value(self, value):
        """
        Returns the cell value. The naive implementation is just returning
          the serialized value.
        :param value: value to be rendered.
        :return: an appropriate value to be used as cell value.
        """

        return self._serialize_value(value)

    @property
    def key(self):
        return self._key

    @property
    def text(self):
        return self._text

    def get_attachment_content_type(self, request):
        """
        Content-Type to be used for the attachment.
        :param request: Request being processed
        :return: A string being a MIME type.
        """

        return self.content_type

    def get_list_report(self, request):
        """
        Fields this report will handle.
        :param request: If the overriden logic will depend on the request.
        :return: A list of strings with fields to report.
        """

        return self.list_report

    def get_report_column_builders(self, request, model):
        """
        Returns builders for column names and column values
          for the elements, being each element like this:
          1. A header fetcher: will retrieve the title for the column.
          2. A value fetcher: will retrieve the value for the column.
        :param model: model to analyze and fetch.
        :param request: current request being processed.
        :return: A list of TrackingReportColumn pairs.
        """

        meta = model._meta
        field_names = set(field.name for field in meta.fields)
        list_report = self.get_list_report(request) or field_names
        _s = self._cell_value

        def header(list_report_item):
            if list_report_item in field_names:
                return text_type(capfirst(meta.get_field(list_report_item).verbose_name))
            else:
                if isinstance(list_report_item, string_types):
                    # model member (method or property)
                    model_member = getattr(model, list_report_item, None)
                    # method check
                    if functions.is_method(model_member, functions.METHOD_UNBOUND|functions.METHOD_INSTANCE):
                        return text_type(capfirst(getattr(model_member, 'short_description',
                                                          list_report_item.replace('_', ' '))))
                    # property check
                    if isinstance(model_member, property):
                        if model_member.getter:
                            return text_type(capfirst(getattr(model_member, 'short_description',
                                                              list_report_item.replace('_', ' '))))
                        raise ValueError('Property item in `list_report` member, or returned by `get_list_report()` '
                                         'must be readable')
                    # report member (method)
                    report_member = getattr(self, list_report_item, None)
                    if functions.is_method(report_member, functions.METHOD_UNBOUND|functions.METHOD_INSTANCE):
                        return text_type(capfirst(getattr(report_member, 'short_description',
                                                          list_report_item.replace('_', ' '))))

                # regular callable
                if callable(list_report_item):
                    return text_type(capfirst(getattr(list_report_item, 'short_description', None) or
                                              getattr(list_report_item, '__name__', None) or '<unknown>'))

                # invalid value
                raise TypeError('Item in `list_report` member, or returned by `get_list_report()` must be a model '
                                'field name, or model instance method, current report''s instance method, or '
                                'a regular callable')

        def fetcher(list_report_item):
            if list_report_item in field_names:
                return lambda obj: _s(getattr(obj, list_report_item))
            else:
                if isinstance(list_report_item, string_types):
                    # model member (method or property)
                    model_member = getattr(model, list_report_item, None)
                    # method check
                    if functions.is_method(model_member, functions.METHOD_UNBOUND|functions.METHOD_INSTANCE):
                        return lambda obj: _s(getattr(obj, list_report_item)())
                    # property check
                    if isinstance(model_member, property):
                        if model_member.getter:
                            return lambda obj: _s(getattr(obj, list_report_item))
                        raise ValueError('Property item in `list_report` member, or returned by `get_list_report()` '
                                         'must be readable')
                    # report member (method)
                    report_member = getattr(self, list_report_item, None)
                    if functions.is_method(report_member, functions.METHOD_UNBOUND|functions.METHOD_INSTANCE):
                        return lambda obj: _s(getattr(self, list_report_item)(obj))

                # regular callable
                if callable(list_report_item):
                    return lambda obj: _s(list_report_item(obj))

                # invalid value
                raise TypeError('Item in `list_report` member, or returned by `get_list_report()` must be a model '
                                'field name, or model instance method, current report''s instance method, or '
                                'a regular callable')

        return [TrackingReportColumn(header=header(item), fetcher=fetcher(item)) for item in list_report]

    def get_report_data_rows(self, request, queryset):
        """
        Using the builders for the queryset model, iterates over the queryset to generate a result
          with headers and rows. This queryset must be the exact same received in the .process method,
          which tells us that this function should be called inside .process implementation.
        :param queryset: Provided queryset
        :return: Result with headers and rows
        """

        model = queryset.model
        meta = model._meta
        field_names = set(field.name for field in meta.fields)
        list_report = self.get_list_report(request) or field_names
        queried_field_named = [l for l in list_report if l in field_names] or ['id']

        columns = self.get_report_column_builders(request, model)
        headers = [column.header for column in columns]
        rows = []
        for instance in queryset.only(*queried_field_named):
            rows.append([column.fetcher(instance) for column in columns])

        return TrackingReportResult(headers=headers, values=rows)

    @abstractmethod
    def get_attachment_filename(self, request, period):
        """
        Filename to be used for the attachment
        :param request: Requset being processed.
        :param period: Period being queried.
        :return: A string with the filename.
        """

        return 'override.me'

    @abstractmethod
    def dump_report_content(self, request, result):
        """
        Dumps the content to a string, suitable to being written on a file.
        :param request: Request being processed.
        :param result: Result being dumped.
        :return: Dumped string.
        """

        return b''

    def get_attachment_content(self, request, queryset):
        """
        Returns the generated file content.
        :param request: The request being processed.
        :param queryset: The model class being processed.
        :return: The report content (usually expressed in raw bytes but could be unicode as well).
        """

        return self.dump_report_content(request, self.get_report_data_rows(request, queryset))

    def process(self, request, queryset, period):
        """
        Will process the request and return an appropriate Response object.
        :param request: The request being processed.
        :param model: The model class being processed.
        :param period: The model being processed.
        :return: The response with the report.
        """

        response = HttpResponse(content=self.get_attachment_content(request, queryset) or '',
                                content_type=self.get_attachment_content_type(request) or 'text/plain')
        response['Content-Disposition'] = 'attachment; filename=' + (self.get_attachment_filename(request, period) or
                                                                     'report.txt')
        return response


class RichFormatTrackingReport(TrackingReport):
    """
    This report class allows specifying format for each cell. Plain-text reports
      do not descend from this subclass, but excel formats do.
    """

    def _cell_value(self, value):
        """
        Returns both the regular value and the serialized one.
        :param value: The regular value.
        :return: (regular, serialized)
        """

        return value, self._serialize_value(value)

    @abstractmethod
    def get_cell_format(self, request, column_spec, column_display, column_index, row_index,
                        cell_value, cell_serialized_value):
        """
        Gets data for the format to be used when formatting the cell.
        :param request: The request being processed.
        :param column_spec: The current column, as returned as item in by `get_list_report()`.
        :param column_display: The current column display text.
        :param column_index: The current column index.
        :param row_index: The 0-based row index. None if processing a header cell.
        :param cell_value: The cell value (not serialized). None if processing a header cell.
        :param cell_serialized_value: The cell serialized value (applies to, say, dates).
          None if processing a header cell.
        :return: The returned data is arbitrary, and according to the underlying
          report class.
        """

        return None


class CSVReport(TrackingReport):
    """
    CSV dumping report. No plugins required for it.
    """

    csv_kwargs = {}

    def get_attachment_filename(self, request, period):
        """
        Filename to be used for the attachment
        :param request: Requset being processed.
        :param period: Period being queried.
        :return: A string with the filename.
        """

        return 'report-%s.csv' % now().strftime("%Y%m%d%H%M%S")

    def dump_report_content(self, request, result):
        """
        Dumps the content to a string, suitable to being written on a file.
        :param result: The result being processed.
        :return: string
        """

        output = StringIO()
        writer = csv.writer(output, **self.csv_kwargs)
        writer.writerows([result.headers] + result.values)
        return output.getvalue()
