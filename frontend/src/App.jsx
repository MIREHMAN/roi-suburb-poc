import { useEffect, useMemo, useState } from 'react'

const API_BASE = 'http://localhost:8000'

function pct(value) {
    return `${((value || 0) * 100).toFixed(2)}%`
}

function App() {
    const [suburbs, setSuburbs] = useState([])
    const [suburbsLoading, setSuburbsLoading] = useState(false)

    const [search, setSearch] = useState('')
    const [minRoi, setMinRoi] = useState('')
    const [maxPrice, setMaxPrice] = useState('')
    const [minSeifa, setMinSeifa] = useState('')
    const [topN, setTopN] = useState(30)

    const [featureMeta, setFeatureMeta] = useState([])
    const [suburbNames, setSuburbNames] = useState([])
    const [selectedSuburb, setSelectedSuburb] = useState('')
    const [featureToAdd, setFeatureToAdd] = useState('')
    const [activeFeatures, setActiveFeatures] = useState([])
    const [featureValues, setFeatureValues] = useState({})

    const [prediction, setPrediction] = useState(null)
    const [predictionLoading, setPredictionLoading] = useState(false)

    const [opportunities, setOpportunities] = useState([])
    const [summary, setSummary] = useState(null)
    const [health, setHealth] = useState(null)
    const [modelInfo, setModelInfo] = useState(null)

    const [banner, setBanner] = useState({ type: '', message: '' })

    const featureMetaMap = useMemo(() => {
        const map = {}
        featureMeta.forEach((f) => {
            map[f.feature] = f
        })
        return map
    }, [featureMeta])

    const showBanner = (type, message) => {
        setBanner({ type, message })
        window.clearTimeout(window._bannerTimer)
        window._bannerTimer = window.setTimeout(() => {
            setBanner({ type: '', message: '' })
        }, 3000)
    }

    const buildFilterParams = () => {
        const params = new URLSearchParams()
        if (search) params.append('name', search)
        if (minRoi) params.append('min_roi', minRoi)
        if (maxPrice) params.append('max_price', maxPrice)
        if (minSeifa) params.append('min_seifa', minSeifa)
        params.append('top_n', topN)
        return params
    }

    const fetchSuburbs = async () => {
        setSuburbsLoading(true)
        try {
            const params = buildFilterParams()
            const response = await fetch(`${API_BASE}/api/suburbs?${params.toString()}`)
            if (!response.ok) throw new Error(`suburbs failed: ${response.status}`)
            const data = await response.json()
            setSuburbs(data)
        } catch (error) {
            console.error('Failed to load suburbs', error)
            showBanner('error', 'Failed to load suburbs from API.')
        } finally {
            setSuburbsLoading(false)
        }
    }

    const downloadReport = async (format) => {
        try {
            const params = buildFilterParams()
            const response = await fetch(`${API_BASE}/api/report/${format}?${params.toString()}`)
            if (!response.ok) throw new Error(`download failed: ${response.status}`)

            const blob = await response.blob()
            const url = window.URL.createObjectURL(blob)
            const disposition = response.headers.get('content-disposition') || ''
            const match = disposition.match(/filename=([^;]+)/)
            const fallback = `suburb_recommendation_report.${format}`
            const filename = match ? match[1].replace(/"/g, '') : fallback

            const a = document.createElement('a')
            a.href = url
            a.download = filename
            document.body.appendChild(a)
            a.click()
            a.remove()
            window.URL.revokeObjectURL(url)
            showBanner('success', `${format.toUpperCase()} report downloaded.`)
        } catch (error) {
            console.error('Report download failed', error)
            showBanner('error', 'Report download failed.')
        }
    }

    const fetchFeatureMetadata = async () => {
        const response = await fetch(`${API_BASE}/api/features`)
        const data = await response.json()
        const features = data.features || []
        setFeatureMeta(features)

        if (features.length > 0 && activeFeatures.length === 0) {
            const defaultFeatures = features.slice(0, 6).map((f) => f.feature)
            setActiveFeatures(defaultFeatures)
            setFeatureToAdd(features[0].feature)

            const defaults = {}
            features.forEach((f) => {
                defaults[f.feature] = f.median
            })
            setFeatureValues(defaults)
        }
    }

    const fetchSuburbNames = async () => {
        const response = await fetch(`${API_BASE}/api/suburb-names?limit=1000`)
        const data = await response.json()
        setSuburbNames(data.names || [])
    }

    const fetchOpportunities = async () => {
        const response = await fetch(`${API_BASE}/api/opportunities?top_n=20`)
        const data = await response.json()
        setSummary(data.summary || null)
        setOpportunities(data.opportunities || [])
    }

    const fetchStatus = async () => {
        const [hRes, mRes] = await Promise.all([
            fetch(`${API_BASE}/api/health`),
            fetch(`${API_BASE}/api/model-info`),
        ])
        setHealth(await hRes.json())
        setModelInfo(await mRes.json())
    }

    const runPrediction = async (overrideFeatures = null) => {
        setPredictionLoading(true)
        try {
            const payload = {
                suburb_name: selectedSuburb || null,
                feature_values:
                    overrideFeatures ||
                    activeFeatures.reduce((acc, feature) => {
                        const raw = featureValues[feature]
                        if (raw !== undefined && raw !== '') acc[feature] = Number(raw)
                        return acc
                    }, {}),
            }

            const response = await fetch(`${API_BASE}/api/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            })
            const data = await response.json()
            if (data.error) throw new Error(data.error)
            setPrediction(data)

            if (data.input_features) {
                setFeatureValues((prev) => ({ ...prev, ...data.input_features }))
            }
            showBanner('success', 'Prediction completed.')
        } catch (error) {
            console.error('Prediction failed', error)
            showBanner('error', 'Prediction failed. Check backend/model status.')
        } finally {
            setPredictionLoading(false)
        }
    }

    const useSuburbDefaults = async () => {
        await runPrediction({})
    }

    const applyScenarioPreset = (preset) => {
        const next = { ...featureValues }
        const setIf = (k, v) => {
            if (featureMetaMap[k]) next[k] = v
        }

        if (preset === 'balanced') {
            setIf('Rent_to_Income_Ratio', 0.22)
            setIf('Working_Age_Share', 0.38)
            setIf('IRSD_Score', 1050)
            setIf('Median_tot_hhd_inc_weekly', 2500)
        }
        if (preset === 'growth') {
            setIf('Working_Age_Share', 0.45)
            setIf('Diversity_Share', 0.4)
            setIf('IRSAD_Score', 1120)
            setIf('Median_tot_hhd_inc_weekly', 3200)
        }
        if (preset === 'defensive') {
            setIf('Senior_Share', 0.24)
            setIf('IRSD_Score', 1100)
            setIf('Rent_to_Income_Ratio', 0.19)
            setIf('Average_household_size', 2.8)
        }
        setFeatureValues(next)
    }

    const addFeature = () => {
        if (!featureToAdd || activeFeatures.includes(featureToAdd)) return
        setActiveFeatures((prev) => [...prev, featureToAdd])
    }

    const removeFeature = (feature) => {
        setActiveFeatures((prev) => prev.filter((f) => f !== feature))
    }

    useEffect(() => {
        fetchSuburbs()
        fetchFeatureMetadata()
        fetchSuburbNames()
        fetchOpportunities()
        fetchStatus()
    }, [])

    return (
        <div className="app-shell">
            <header className="hero">
                <h1>Suburb ROI Intelligence Dashboard</h1>
                <p>Test scenarios, compare opportunities, and export reports from the active filter state.</p>
                <div className="status-grid">
                    <div>
                        <span>API Status</span>
                        <strong>{health?.status || '...'}</strong>
                    </div>
                    <div>
                        <span>Suburbs Loaded</span>
                        <strong>{health?.suburbs_loaded ?? '...'}</strong>
                    </div>
                    <div>
                        <span>Model Target</span>
                        <strong>{modelInfo?.target || '...'}</strong>
                    </div>
                    <div>
                        <span>Model R2</span>
                        <strong>{modelInfo?.metrics?.r2 !== undefined ? modelInfo.metrics.r2.toFixed(3) : '...'}</strong>
                    </div>
                </div>
            </header>

            {banner.message ? <div className={`banner ${banner.type}`}>{banner.message}</div> : null}

            <section className="panel">
                <div className="panel-head">
                    <h2>Opportunity Explorer</h2>
                    <button onClick={() => { fetchSuburbs(); fetchOpportunities() }}>Refresh Insights</button>
                </div>
                <div className="controls-grid">
                    <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Suburb name" />
                    <input value={minRoi} onChange={(e) => setMinRoi(e.target.value)} type="number" placeholder="Min ROI %" />
                    <input value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)} type="number" placeholder="Max monthly mortgage" />
                    <input value={minSeifa} onChange={(e) => setMinSeifa(e.target.value)} type="number" placeholder="Min SEIFA" />
                    <input value={topN} onChange={(e) => setTopN(Number(e.target.value || 30))} type="number" min="5" max="200" placeholder="Top N" />
                    <button onClick={fetchSuburbs}>{suburbsLoading ? 'Loading...' : 'Apply Filters'}</button>
                </div>
                <div className="report-actions">
                    <button className="report-btn" onClick={() => downloadReport('csv')}>Download Report (CSV)</button>
                    <button className="report-btn alt" onClick={() => downloadReport('pdf')}>Download Report (PDF)</button>
                </div>

                <div className="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Suburb</th>
                                <th>Predicted ROI</th>
                                <th>Mortgage</th>
                                <th>Weekly Rent</th>
                                <th>SEIFA</th>
                            </tr>
                        </thead>
                        <tbody>
                            {suburbs.map((s) => (
                                <tr key={`${s.name}-${s.price}`}>
                                    <td>{s.name}</td>
                                    <td className="good">{pct(s.roi)}</td>
                                    <td>${Number(s.price || 0).toLocaleString()}</td>
                                    <td>${Number(s.rent || 0).toLocaleString()}</td>
                                    <td>{Number(s.seifa_score || 0).toFixed(0)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {!suburbsLoading && suburbs.length === 0 ? <p className="muted">No suburbs found for current filters.</p> : null}
                </div>
            </section>

            <section className="panel two-col">
                <div>
                    <h2>Prediction Sandbox</h2>
                    <div className="field-group">
                        <label>Select suburb baseline</label>
                        <input
                            list="suburb-options"
                            value={selectedSuburb}
                            onChange={(e) => setSelectedSuburb(e.target.value)}
                            placeholder="Type suburb name"
                        />
                        <datalist id="suburb-options">
                            {suburbNames.map((name) => (
                                <option key={name} value={name} />
                            ))}
                        </datalist>
                        <button onClick={useSuburbDefaults} disabled={!selectedSuburb || predictionLoading}>Use Suburb Defaults</button>
                    </div>

                    <div className="preset-row">
                        <button onClick={() => applyScenarioPreset('balanced')}>Balanced Preset</button>
                        <button onClick={() => applyScenarioPreset('growth')}>Growth Preset</button>
                        <button onClick={() => applyScenarioPreset('defensive')}>Defensive Preset</button>
                    </div>

                    <div className="field-group">
                        <label>Add feature to scenario</label>
                        <div className="inline-row">
                            <select value={featureToAdd} onChange={(e) => setFeatureToAdd(e.target.value)}>
                                {featureMeta.map((f) => (
                                    <option key={f.feature} value={f.feature}>{f.feature}</option>
                                ))}
                            </select>
                            <button onClick={addFeature}>Add Feature</button>
                        </div>
                    </div>

                    <div className="feature-list">
                        {activeFeatures.map((feature) => {
                            const meta = featureMetaMap[feature] || {}
                            return (
                                <div className="feature-card" key={feature}>
                                    <div className="feature-head">
                                        <strong>{feature}</strong>
                                        <button className="ghost" onClick={() => removeFeature(feature)}>Remove</button>
                                    </div>
                                    <input
                                        type="number"
                                        value={featureValues[feature] ?? ''}
                                        onChange={(e) => setFeatureValues((prev) => ({ ...prev, [feature]: e.target.value }))}
                                    />
                                    <small>
                                        Range: {meta.min ?? '-'} to {meta.max ?? '-'} | Median: {meta.median ?? '-'}
                                    </small>
                                </div>
                            )
                        })}
                    </div>

                    <button className="cta" onClick={() => runPrediction()} disabled={predictionLoading}>
                        {predictionLoading ? 'Predicting...' : 'Run ROI Prediction'}
                    </button>
                </div>

                <div>
                    <h2>Prediction Insights</h2>
                    {prediction ? (
                        <div className="insight-card">
                            <div className="metric-grid">
                                <div>
                                    <span>Predicted ROI</span>
                                    <strong>{prediction.predicted_roi_percent}%</strong>
                                </div>
                                <div>
                                    <span>Percentile</span>
                                    <strong>{prediction.percentile_vs_all_suburbs}%</strong>
                                </div>
                                <div>
                                    <span>Signal</span>
                                    <strong>{prediction.investment_signal}</strong>
                                </div>
                            </div>

                            <h3>Top Drivers</h3>
                            <ul className="drivers">
                                {(prediction.top_factors || []).map((factor) => (
                                    <li key={factor.feature}>
                                        <span>{factor.feature}</span>
                                        <span className={factor.effect === 'positive' ? 'good' : 'warn'}>
                                            {factor.effect}
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ) : (
                        <p className="muted">No prediction yet. Select suburb/features and run simulation.</p>
                    )}
                </div>
            </section>

            <section className="panel">
                <h2>Investment Opportunity Insights</h2>
                {summary && (
                    <div className="summary-grid">
                        <div><span>Suburbs Analyzed</span><strong>{summary.suburbs_analyzed}</strong></div>
                        <div><span>Top-20 Avg ROI</span><strong>{summary.avg_roi_percent_top_n}%</strong></div>
                        <div><span>Median ROI (All)</span><strong>{summary.median_roi_percent_all}%</strong></div>
                        <div><span>Max ROI</span><strong>{summary.max_roi_percent}%</strong></div>
                    </div>
                )}

                <div className="opportunity-grid">
                    {opportunities.slice(0, 12).map((o) => (
                        <article key={o.name} className="op-card">
                            <h3>{o.name}</h3>
                            <p>ROI: <strong>{pct(o.roi)}</strong></p>
                            <p>Mortgage: ${Number(o.price || 0).toLocaleString()}</p>
                            <p>Rent: ${Number(o.rent || 0).toLocaleString()}</p>
                            <div className="tag-row">
                                {(o.insight_tags || []).map((tag) => (
                                    <span key={tag} className="tag">{tag}</span>
                                ))}
                            </div>
                        </article>
                    ))}
                </div>
            </section>
        </div>
    )
}

export default App
