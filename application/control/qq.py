#-*- coding: utf-8 -*-

from application import app
from flask import request
from flask import render_template
from flask import session

from application.apps import dianzan
import sys

from application.apps.db_methods import add_task
from application.apps.db_methods import init_db
import logging
import traceback
from pprint import pprint as printf
import urllib
import json

from application.control import kvdbwrap

@app.route('/dianzan', methods = ['POST'])
def _dianzan():
    try:
        qq = request.form.get('qq', '')
        pwd = request.form.get('pwd', '')
        cnt = request.form.get('cnt', '1')
        feq = request.form.get('feq', '10')  # 点赞次数
        inc = request.form.get('inc', '10')
        frr = request.form.get('frr', '')
        pos = request.form.get('pos', '')
        neg = request.form.get('neg', '')
        remember = request.form.get('remember', '')
        _url = None
        data = {}
        data['remember'] = remember
        if remember == "on" and session.get('qq') == qq:
          with kvdbwrap.KVDB() as kv:
            try:
              ret = kv.get('qq#%s' % qq)
              data = json.loads(ret)
            except Exception as e:
              print str(e)
              import sys, traceback
              traceback.print_exc(file=sys.stdout)
          data['remember'] = 'on'
        else:
          if 'qq' in session:
            session.pop('qq', None)

        data.update({
          'qq': qq,
          'pwd': pwd,
          'cnt': cnt,
          'feq': feq,
          'inc': inc,
          'frr': frr,
          'pos': pos,
          'neg': neg
          })
        try:
          D = dianzan.Dianzan(**data)
          #D = dianzan.Dianzan(
          #                    qq = qq, 
          #                    pwd = pwd,
          #                    cnt = int(cnt),
          #                    feq = int(feq),
          #                    inc = int(inc),
          #                    pos = pos,
          #                    neg = neg,
          #                    url = _url
          #                    )
        except Exception as e:
          import traceback, sys
          print e
          traceback.print_exc(file = sys.stdout)


        ret = D.dianzan(cnt = int(cnt))

        try:
            feq = int(feq)
            inc = int(inc)

            if (feq * inc - inc) > 0:
                db = init_db()
                add_task(db, uid = D.qq, url = D.url, ttl = feq * inc - inc, inc = inc, pos = pos, neg = neg)
        except Exception as e:
            logging.error('/dianzan:' + str(e))
            traceback.print_exc(file=sys.stdout)

        if str(frr) == "on":
            try:ret = D.get_friend()
            except:ret={}
            if len(ret) == 0:
                return '''
                        <html>
                        <body>
                            </p>妈蛋, 好像获取好友列表失败了,<a href="/">再试一次</a>吧</p>
                        </body>
                        </html>

                        '''
            return render_template('select_friend.html', frr = ret)

    except Exception as e:
        #logging.error(str(e))
        print str(e)
        import traceback, sys
        traceback.print_exc(file=sys.stdout)
        ret = "<p>%s</p>"%("用户名，密码或者验证码错误!请再试一次")
        ret += '<script> console.log("%s") </script>' % str(e)
    return ret

@app.route('/dianzan_verify', methods = ['POST'])
def _dianzan_verify():
    headers = dict()
    headers['Origin'] = 'http://pt.3g.qq.com'
    headers['Host'] = 'pt.3g.qq.com'
    #headers['User-Agent'] = 'curl/7.21.3 (i686-pc-linux-gnu) libcurl/7.21.3 OpenSSL/0.9.8o zlib/1.2.3.4 libidn/1.18'
    headers['User-Agent'] = ''

    data = dict()
    try:
        for i in request.form:
            data[i] = request.form[i]
        D = dianzan.Dianzan_verify()
        D.verify(data = data, headers = headers)
        ret = D.dianzan()
    except Exception as e:
        #logging.error(str(e) + str(data))
        print str(e) + str(data)
        traceback.print_exc(file=sys.stdout)
        ret = "<p>%s</p>"%("用户名，密码或者验证码错误!请再试一次")
        ret += '<script> console.log("%s") </script>' % str(e)
    return ret


@app.route('/select_friend', methods = ['POST'])
def select_friend():
    printf(request.form.keys())
    return 'yes'

@app.route('/feedback', methods = ['POST'])
def feedback():
    db = init_db()
    nickname = request.form.get('nickname', '这个人很懒什么都没留下').strip()  # T_T  这样不管用,,当为空时得到的就是空字符串,,,我这个傻逼
    contact = request.form.get('contact', '这个人很懒什么都没留下').strip()
    comment = request.form.get('comment', '妈蛋, 这个人什么都没写').strip()

    if not nickname: nickname = '这个人很懒什么都没留下'
    if not contact: contact = '这个人很懒什么都没留下'
    if not comment: comment = '妈蛋,这个人太懒了吧! 什么都没写...'

    import MySQLdb
    nickname = MySQLdb.escape_string(nickname)
    contact = MySQLdb.escape_string(contact)
    comment = MySQLdb.escape_string(comment)
    sql = r'''
                insert feedback (nickname, contact, comment) values ("%s", "%s", "%s");
        ''' % (nickname, contact, comment)
    cursor = db.cursor()
    cursor.execute(sql)
    db.commit()
    db.close()
    return r'''
        <html>
            <p> 评论成功, <a href="/">点击</a>返回  </p>
        </html>
    '''
