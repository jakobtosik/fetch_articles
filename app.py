from flask import Flask, request, jsonify, make_response
import requests
import csv
import io

app = Flask(__name__)

@app.route('/fetch_articles', methods=['POST'])
def fetch_articles():
    # Get JSON data from request
    data = request.json
    subdomain = data.get('subdomain')
    api_token = data.get('api_token')
    email = data.get('email')

    if not all([subdomain, api_token, email]):
        return jsonify({"error": "Missing required fields"}), 400

    # API endpoint
    url = f'https://{subdomain}.zendesk.com/api/v2/help_center/articles.json'

    # Create an in-memory CSV file
    output = io.StringIO()
    writer = csv.writer(output)

    # Write the header
    writer.writerow(['ID', 'Title', 'Body', 'Created At', 'Updated At'])

    # Pagination variables
    while url:
        response = requests.get(url, auth=(email, api_token))
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])

            # Write article data to CSV
            for article in articles:
                writer.writerow([
                    article['id'],
                    article['title'],
                    article['body'],
                    article['created_at'],
                    article['updated_at']
                ])

            # Pagination control
            url = data.get('meta', {}).get('has_more') and data.get('meta', {}).get('next_page')
        else:
            return jsonify({"error": f"Failed to retrieve articles: {response.status_code}", "details": response.text}), 500

    # Prepare CSV response as downloadable attachment
    output.seek(0)  # Go to the beginning of the file
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=zendesk_articles.csv"
    response.headers["Content-type"] = "text/csv"
    return response

if __name__ == '__main__':
    app.run(debug=True)
