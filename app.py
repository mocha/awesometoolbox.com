from flask import Flask, flash, redirect, render_template, request, url_for, g, jsonify, json
from rethinkdb import r
from forms import ToolForm
from helpers import url_exists

RDB_HOST = 'localhost'
RDB_PORT = 28015
DB_NAME = 'awesometoolbox'


def dbSetup():
    connection = r.connect(host=RDB_HOST, port=RDB_PORT)
    try:
        connection.run(r.db_create(DB_NAME))
        connection.run(r.db(DB_NAME).table_create('tools'))
        connection.run(r.db(DB_NAME).table_create('users'))
        connection.run(r.db(DB_NAME).table_create('categories'))
        connection.run(r.db(DB_NAME).table_create('toolboxes'))
        print 'Database setup completed. Now run the app without --setup.'
    except Exception:
        print 'App database already exists. Run the app without --setup.'
    finally:
        connection.close()


app = Flask(__name__)

# app settings

app.secret_key = 'Jordan is a bozo'



# db setup and teardown stuff

@app.before_request
def before_request():
    g.rdb_conn = r.connect(host=RDB_HOST, port=RDB_PORT, db_name=DB_NAME)

@app.teardown_request
def teardown_request(exception):
    g.rdb_conn.close()



# context processors

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



# actual app views begin
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

    if request.form:
        form = request.form
    else:
        form = ToolForm()

    if request.method == 'POST':
        
        if not request.form['name'] or not request.form['description'] or not request.form['category'] or not request.form['link']:
            flash('This form isn\'t very long. Go ahead and try again.', 'error')

        elif r.table('tools').filter({'name':request.form['name']}).count().run(g.rdb_conn) != 0:
            flash('That tool already seems to exist.', 'error')

        elif not url_exists(request.form['link']):
            flash('That url doesn\'t seem quite right.', 'error')

        else:
            slug = sub('[^A-Za-z0-9]+', '', request.form['name'].lower())

            insertion = r.table('tools').insert({
                       'name': request.form['name'], # todo: need to make this check for uniqueness
                'description': request.form['description'],
                   'category': request.form['category'].replace(", ", ",").split(','), 
                       'link': request.form['link'],
                       'slug': slug,
            }).run(g.rdb_conn)

            if insertion['errors'] == 0:
                flash('Thanks for adding your tool!', 'success')
                return redirect('/tool/' + str(insertion['generated_keys'][0]) + "/" + slug)
                    # return redirect(url_for('toolpage', tool_id = str(insertion['generated_keys'][0])))
                    # should be using url_for as above, but it kept throwing a builderror
            
            else: flash('AH FUCK', 'error')

    return render_template('tool_form.html', form=form)



@app.route('/tool/<tool_id>/delete')
def delete_tool(tool_id):
    # todo: should be checking for user auth
    deleted = r.table('tools').get(tool_id).delete().run(g.rdb_conn)
    if deleted['deleted'] == 1:
        flash('That shit is gooooooone.', 'success')
    else:
        flash('It wasn\'t deleted! Oh my!', 'error')
    
    return redirect(url_for('homepage'))


from random import choice
@app.route('/tool/<tool_id>/<toolname>')
def toolpage(toolname, tool_id):
    tab = ""
    tool = r.table('tools').get(tool_id).run(g.rdb_conn)
    page_title = tool['name']
    related_category = choice(tool['category'])

    related_tools = r.table('tools').filter(lambda row: row['category'].filter(lambda attr: attr == related_category).count() > 0).filter(lambda row: row['name']!=tool['name']).pluck('name').run()
    if list(related_tools).__len__() == 0: related_tools = False

    return render_template('tool_page.html', 
                  tab = tab, 
           page_title = page_title, 
                 tool = tool,
     related_category = related_category,
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
