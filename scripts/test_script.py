import requests

BASE_URL = 'http://localhost:8000'


def check_health() -> None:
    r = requests.get(f'{BASE_URL}/api/health', timeout=20)
    r.raise_for_status()
    print('Health:', r.json())


def check_top_suburbs() -> None:
    params = {
        'top_n': 5,
        'min_roi': 10,
    }
    r = requests.get(f'{BASE_URL}/api/suburbs', params=params, timeout=30)
    r.raise_for_status()
    rows = r.json()
    print(f'Returned suburbs: {len(rows)}')
    for i, row in enumerate(rows, 1):
        print(f"{i}. {row.get('name')} | ROI={(row.get('roi', 0) * 100):.2f}% | Rent=${row.get('rent', 0)}")

def check_features_and_prediction() -> None:
    feature_resp = requests.get(f'{BASE_URL}/api/features', timeout=30)
    feature_resp.raise_for_status()
    features = feature_resp.json().get('features', [])
    print(f'Features available: {len(features)}')
    if not features:
        return

    payload = {
        'suburb_name': None,
        'feature_values': {
            features[0]['feature']: features[0]['median'],
        },
    }
    pred_resp = requests.post(f'{BASE_URL}/api/predict', json=payload, timeout=30)
    pred_resp.raise_for_status()
    prediction = pred_resp.json()
    print('Prediction:', prediction.get('predicted_roi_percent'), prediction.get('investment_signal'))


def check_opportunities() -> None:
    resp = requests.get(f'{BASE_URL}/api/opportunities', params={'top_n': 10}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    print('Opportunity summary:', data.get('summary', {}))
    print('Opportunity count:', len(data.get('opportunities', [])))

def check_report_exports() -> None:
    csv_resp = requests.get(f'{BASE_URL}/api/report/csv', params={'min_roi': 10, 'top_n': 10}, timeout=40)
    csv_resp.raise_for_status()
    print('CSV export content-type:', csv_resp.headers.get('content-type'))
    print('CSV export bytes:', len(csv_resp.content))

    pdf_resp = requests.get(f'{BASE_URL}/api/report/pdf', params={'min_roi': 10, 'top_n': 10}, timeout=40)
    pdf_resp.raise_for_status()
    print('PDF export content-type:', pdf_resp.headers.get('content-type'))
    print('PDF export bytes:', len(pdf_resp.content))


if __name__ == '__main__':
    check_health()
    check_top_suburbs()
    check_features_and_prediction()
    check_opportunities()
    check_report_exports()
