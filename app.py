from flask import Flask, flash, redirect, render_template, request, url_for, g, jsonify, json
from rethinkdb import r

RDB_HOST = 'localhost'
RDB_PORT = 28015
DB_NAME = 'awesometoolbox'


def dbSetup():
    connection = r.connect(host=RDB_HOST, port=RDB_PORT)
    try:
        connection.run(r.db_create(DB_NAME))
        connection.run(r.db(DB_NAME).table_create('tools'))
        print 'Database setup completed. Now run the app without --setup.'
    except Exception:
        print 'App database already exists. Run the app without --setup.'
    finally:
        connection.close()


app = Flask(__name__)
app.secret_key = 'Jordan is a bozo'


@app.before_request
def before_request():
    g.rdb_conn = r.connect(host=RDB_HOST, port=RDB_PORT, db_name=DB_NAME)

@app.teardown_request
def teardown_request(exception):
    g.rdb_conn.close()



@app.route('/')
def homepage():
    tab = ""
    page_title = "Latest Tools"
    page_subtitle = "Check out all the latest tools that have been added to awesometoolbox."
    tools = r.table('tools').run(g.rdb_conn)

    return render_template('tool_listing.html', 
        tab=tab, 
        tools = tools,
        page_title=page_title, 
        page_subtitle=page_subtitle
    )



@app.route('/tool/<tool_id>/<toolname>')
def toolpage(toolname, tool_id):
    tab = ""
    tool = r.table('tools').get(tool_id).run(g.rdb_conn)
    page_title = tool['name']

    return render_template('tool_page.html', 
        tab=tab, 
        page_title=page_title, 
        tool = tool
    )   



@app.route('/toolbox/<toolboxname>')
def toolboxpage(toolboxname):
    tab = toolboxname
    page_title = toolboxname
    page_subtitle = "Created by Patrick Deuley on 12/30/2012. Last Updated on 2/12/2013."
    return render_template('tool_listing.html', 
        tab=tab, 
        page_title=page_title, 
        page_subtitle=page_subtitle
    )



@app.route('/category/<category_name>')
def categorypage(category_name):
    tab = category_name
    page_title = category_name
    tools = r.table('tools').filter(lambda tool: tool['category'].contains(category_name)).run(g.rdb_conn)
    return render_template('tool_listing.html', 
        tab=tab, 
        page_title=page_title, 
        tools = tools,
    )



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
