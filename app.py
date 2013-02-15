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

@app.context_processor
def pull_categories():

    # pull all categories from all tools
    # todo: gotta fix this, it's a terrible way to approach this
    categories = set()
    all_categories = r.table('tools').filter(lambda row: row['category'].count() > 0).pluck('category').run(g.rdb_conn)
    for categoryset in all_categories:
        for item in categoryset['category']:
            categories.add(item)

    return dict({'categories': sorted(categories)})

@app.route('/')
def homepage():
    tab = ""
    page_title = "Latest Tools"
    page_subtitle = "Check out all the latest tools that have been added to awesometoolbox."
    tools = r.table('tools').order_by('name').run(g.rdb_conn)

    return render_template('tool_listing.html', 
        tab=tab, 
        tools = tools,
        page_title=page_title, 
        page_subtitle=page_subtitle,
    )



from re import sub
@app.route('/tool/new', methods=['GET', 'POST'])
def new_tool():
    
    page_title = "Add tool"

    if request.method == 'POST':
        
        # todo: should be checking for user auth

        slug = sub('[^A-Za-z0-9]+', '', request.form['name'].lower())

        insertion = r.table('tools').insert({
                   'name': request.form['name'], # todo: need to make this check for uniqueness
            'description': request.form['description'],
               'category': request.form['category'].replace(", ", ",").split(','), 
                   'link': request.form['link'],
                   'slug': slug , # todo: need to make this check for uniqueness
        }).run(g.rdb_conn)

        if insertion['errors'] == 0:
            flash('Thanks for adding your tool!', 'success')
            return redirect('/tool/' + str(insertion['generated_keys'][0]) + "/" + slug)
                # return redirect(url_for('toolpage', tool_id = str(insertion['generated_keys'][0])))
                # should be using url_for as above, but it kept throwing a builderror
        
        else: flash('There was some sort of error that happened. :-(', 'error')

    return render_template('tool_form.html')



@app.route('/tool/<tool_id>/delete')
def delete_tool(tool_id):
    # todo: should be checking for user auth
    deleted = r.table('tools').get(tool_id).delete().run(g.rdb_conn)
    if deleted['deleted'] == 1:
        flash('That shit is gooooooone.', 'success')
    else:
        flash('It wasn\'t deleted! Oh my!', 'error')
    
    return redirect(url_for('homepage'))



@app.route('/tool/<tool_id>/<toolname>')
def toolpage(toolname, tool_id):
    tab = ""
    tool = r.table('tools').get(tool_id).run(g.rdb_conn)
    page_title = tool['name']

    related_tools = "foo" #should pick a random category and pull 5 tools from it

    return render_template('tool_page.html', 
                  tab = tab, 
           page_title = page_title, 
                 tool = tool,
        related_tools = related_tools,
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
    tools = r.table('tools').filter(
        lambda row: row['category'].filter(lambda attr: attr == category_name).count() > 0
    ).run(g.rdb_conn)
    return render_template('tool_listing.html', 
        tab=tab, 
        page_title=page_title, 
        tools = tools,
    )




if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
