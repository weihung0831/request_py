from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    # with open('requests_test.py','r') as file:
    #     exec(file.read())
    return render_template('home.html')
# def run_dataGet():
#     with open('/requests_test.py','r') as file:
#         exec(file.read())
#     return

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
