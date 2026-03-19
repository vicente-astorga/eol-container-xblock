# -*- coding: utf-8 -*-

from mock import patch, Mock


from django.test import TestCase, Client

from common.djangoapps.util.testing import UrlResetMixin
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from xmodule.modulestore.tests.factories import CourseFactory
from common.djangoapps.student.tests.factories import UserFactory, CourseEnrollmentFactory
from xblock.field_data import DictFieldData
from common.djangoapps.student.roles import CourseStaffRole

from .eolcontainer import EolContainerXBlock

from six import text_type

import logging
logger = logging.getLogger(__name__)

XBLOCK_RUNTIME_USER_ID = 99

class TestEolContainerXBlock(UrlResetMixin, ModuleStoreTestCase):

    def make_an_xblock(self, **kw):
        """
        Helper method that creates a EolContainer XBlock
        """
        course = self.course
        runtime = Mock(
            course_id=course.id,
            service=Mock(
                return_value=Mock(_catalog={}),
            ),
            user_id=XBLOCK_RUNTIME_USER_ID,
        )
        scope_ids = Mock()
        field_data = DictFieldData(kw)
        xblock = EolContainerXBlock(runtime, field_data, scope_ids)
        xblock.xmodule_runtime = runtime
        xblock.location = course.id  # Example of location
        xblock._edited_by = XBLOCK_RUNTIME_USER_ID
        return xblock

    def setUp(self):

        super(TestEolContainerXBlock, self).setUp()

        # create a course
        self.course = CourseFactory.create(org='mss', course='999',
                                           display_name='xblock tests')
        # cambio test
        # create Xblock
        self.xblock = self.make_an_xblock()
        # Patch the comment client user save method so it does not try
        # to create a new cc user when creating a django user
        with patch('common.djangoapps.student.models.cc.User.save'):
            uname = 'student'
            email = 'student@edx.org'
            password = 'test'

            # Create and enroll student
            self.student = UserFactory(
                username=uname, password=password, email=email)
            CourseEnrollmentFactory(
                user=self.student, course_id=self.course.id)

            # Create and Enroll staff user
            self.staff_user = UserFactory(
                username='staff_user',
                password='test',
                email='staff@edx.org',
                is_staff=True)
            CourseEnrollmentFactory(
                user=self.staff_user,
                course_id=self.course.id)
            CourseStaffRole(self.course.id).add_users(self.staff_user)

            # Log the student in
            self.client = Client()
            self.assertTrue(self.client.login(username=uname, password=password))

            # Log the user staff in
            self.staff_client = Client()
            self.assertTrue(
                self.staff_client.login(
                    username='staff_user',
                    password='test'))

    def test_workbench_scenarios(self):
        """
            Checks workbench scenarios title and basic scenario
        """
        result_title = 'EolContainerXBlock'
        basic_scenario = "<eolcontainer/>"
        test_result = self.xblock.workbench_scenarios()
        self.assertEqual(result_title, test_result[0][0])
        self.assertIn(basic_scenario, test_result[0][1])


    def test_validate_default_field_data(self):
        """
            Validate that xblock is created successfully
        """
        self.assertEqual(self.xblock.type, 'Exploremos')
        self.assertEqual(self.xblock.text, '<p>Contenido de la capsula.</p>')
        self.assertEqual(self.xblock.case_title, 'Caso')
        self.assertEqual(self.xblock.show_header, True)
        self.assertEqual(self.xblock.show_footer, True)

    def test_student_view(self):
        """
            Check if xblock template loaded correctly
        """
        student_view = self.xblock.student_view()
        student_view_html = student_view.content
        self.assertIn('eolcontainer_block', student_view_html)
