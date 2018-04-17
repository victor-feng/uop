#!/usr/bin/python
# -*- coding: UTF-8 -*-

import logging

import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import parseaddr, formataddr
email_server = 'casarray.syswin.com'
sender = 'zhanghai@syswin.com'
subjects = {
    '100': u'创建虚机成功',
}


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr(
        (
            Header(name, 'utf-8').encode(),
            addr.encode('utf-8') if isinstance(addr, unicode) else addr
        )
    )


class SendEmail(object):

    def __init__(self, username, content, email_address, subject_type):
        self.email_server = email_server
        self.username = username
        self.content = content
        self.email_address = email_address
        self.sender = sender
        self.subjects = subjects
        self.subject = self.subjects.get(subject_type)

    def send_email(self):
        message = MIMEText(
            '尊敬的 %s ：%s' %
            (self.username, self.content), 'plain', 'utf-8'
        )
        message['From'] = _format_addr(u"UOP <%s>" % self.sender)
        message['To'] = Header(self.email_address)
        message['Subject'] = Header(self.subject, 'utf-8')
        try:
            smtpObj = smtplib.SMTP(self.email_server)
            smtpObj.sendmail(
                self.sender, [str(self.email_address)], message.as_string()
            )
            logging.info("[EMAIL] Send email successful.")
            res = True
        except Exception as e:
            logging.exception(
                "[EMAIL] Send email faild. Exception: %s", e.args
            )
            print "Error: 无法发送邮件"
            res = False
        return res


if __name__ == '__main__':

    send = SendEmail(
        username='victor',
        content='create virtual machine successful.',
        email_address='fengyukai@syswin.com',
        subject_type='100'
    )
    send.send_email()
