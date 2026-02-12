import { useEffect, useState } from 'react'

const API_BASE = 'http://localhost:8000'

function roiPercent(value) {
    return `${((value || 0) * 100).toFixed(2)}%`
}

function App() {
    const [suburbNames, setSuburbNames] = useState([])
    const [selectedSuburb, setSelectedSuburb] = useState('')
    const [modelDefaults, setModelDefaults] = useState({})
    const [guidance, setGuidance] = useState({})
    const [userInputs, setUserInputs] = useState({
        monthlyMortgage: '',
        mortgageBurdenPct: '',
        weeklyRent: '',
        seifaScore: '',
        population: '',
        workingAgePct: '',
        seniorPct: '',
        diversityPct: '',
        medianAge: '',
        householdSize: '',
    })

    const [prediction, setPrediction] = useState(null)
    const [opportunities, setOpportunities] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    useEffect(() => {
        const load = async () => {
            try {
                const [featureRes, suburbRes, guidanceRes] = await Promise.all([
                    fetch(`${API_BASE}/api/features`),
                    fetch(`${API_BASE}/api/suburb-names?limit=500`),
                    fetch(`${API_BASE}/api/input-guidance`),
                ])

                const featureData = await featureRes.json()
                const suburbData = await suburbRes.json()
                const guidanceData = await guidanceRes.json()

                const features = featureData.features || []
                const defaults = {}
                features.forEach((f) => {
                    defaults[f.feature] = f.median
                })

                const g = guidanceData.guidance || {}

                setModelDefaults(defaults)
                setSuburbNames(suburbData.names || [])
                setGuidance(g)
                setUserInputs({
                    monthlyMortgage: String(g.monthly_mortgage?.median ?? ''),
                    mortgageBurdenPct: String(g.mortgage_burden_pct?.median ?? 30),
                    weeklyRent: String(g.weekly_rent?.median ?? ''),
                    seifaScore: String(g.seifa_score?.median ?? defaults.IRSD_Score ?? ''),
                    population: String(g.population_size?.median ?? defaults.Tot_P_P ?? ''),
                    workingAgePct: String(g.working_age_pct?.median ?? Number(defaults.Working_Age_Share || 0) * 100),
                    seniorPct: String(g.senior_pct?.median ?? Number(defaults.Senior_Share || 0) * 100),
                    diversityPct: String(g.diversity_pct?.median ?? Number(defaults.Diversity_Share || 0) * 100),
                    medianAge: String(g.median_age_years?.median ?? defaults.Median_age_persons ?? ''),
                    householdSize: String(g.household_size?.median ?? defaults.Average_household_size ?? ''),
                })
            } catch (loadError) {
                console.error(loadError)
                setError('Failed to load form options from the API.')
            }
        }

        load()
    }, [])

    const toNumber = (value, fallback = 0) => {
        const parsed = Number(value)
        return Number.isFinite(parsed) ? parsed : fallback
    }

    const clampShare = (valuePct) => {
        const share = toNumber(valuePct, 0) / 100
        return Math.max(0, Math.min(1, share))
    }

    const rangeLabel = (key, decimals = 0, suffix = '') => {
        const item = guidance[key]
        if (!item) return 'N/A'
        const low = Number(item.min).toFixed(decimals)
        const high = Number(item.max).toFixed(decimals)
        return `${low} - ${high}${suffix}`
    }

    const buildEngineeredFeatures = () => {
        const engineered = { ...modelDefaults }

        const seifa = toNumber(userInputs.seifaScore, engineered.IRSD_Score || 1000)
        const monthlyMortgage = Math.max(1, toNumber(userInputs.monthlyMortgage, guidance.monthly_mortgage?.median || 1))
        const burdenPct = Math.max(5, Math.min(80, toNumber(userInputs.mortgageBurdenPct, 30)))
        const burdenShare = burdenPct / 100
        const householdIncomeWeekly = (monthlyMortgage / burdenShare) * 12 / 52
        const weeklyRent = Math.max(0, toNumber(userInputs.weeklyRent, guidance.weekly_rent?.median || 0))

        engineered.IRSD_Score = seifa
        engineered.IRSAD_Score = seifa
        engineered.IER_Score = seifa
        engineered.IEO_Score = seifa
        engineered.Median_age_persons = toNumber(userInputs.medianAge, engineered.Median_age_persons || 0)
        engineered.Median_tot_hhd_inc_weekly = householdIncomeWeekly
        engineered.Median_tot_prsnl_inc_weekly = householdIncomeWeekly * 0.56
        engineered.Average_household_size = Math.max(0.5, toNumber(userInputs.householdSize, engineered.Average_household_size || 1))
        engineered.Tot_P_P = Math.max(1, toNumber(userInputs.population, engineered.Tot_P_P || 1))
        engineered.Working_Age_Share = clampShare(userInputs.workingAgePct)
        engineered.Senior_Share = clampShare(userInputs.seniorPct)
        engineered.Diversity_Share = clampShare(userInputs.diversityPct)
        engineered.Rent_to_Income_Ratio = Math.min(1.5, weeklyRent / Math.max(1, householdIncomeWeekly))

        return engineered
    }

    const handleSubmit = async (event) => {
        event.preventDefault()
        setLoading(true)
        setError('')

        try {
            const payload = {
                suburb_name: selectedSuburb || null,
                feature_values: buildEngineeredFeatures(),
            }

            const predictRes = await fetch(`${API_BASE}/api/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            })

            const predictData = await predictRes.json()
            if (predictData.error) {
                throw new Error(predictData.error)
            }

            const nearRes = await fetch(
                `${API_BASE}/api/suburbs-near-roi?roi=${encodeURIComponent(predictData.predicted_roi_score)}&top_n=5`,
            )
            const nearData = await nearRes.json()

            setPrediction(predictData)
            setOpportunities(nearData.suburbs || [])
        } catch (submitError) {
            console.error(submitError)
            setError('Prediction failed. Make sure backend and model are running.')
            setPrediction(null)
            setOpportunities([])
        } finally {
            setLoading(false)
        }
    }

    return (
        <main className="app">
            <section className="card">
                <h1>ROI Suburb Predictor</h1>
                <p>Enter investment-focused assumptions. The app engineers model features in the background.</p>

                <form className="form" onSubmit={handleSubmit}>
                    <label>
                        Suburb (optional baseline)
                        <input
                            list="suburb-options"
                            value={selectedSuburb}
                            onChange={(e) => setSelectedSuburb(e.target.value)}
                            placeholder="Type a suburb name"
                        />
                    </label>

                    <datalist id="suburb-options">
                        {suburbNames.map((name) => (
                            <option key={name} value={name} />
                        ))}
                    </datalist>

                    <div className="feature-grid">
                        <label>
                            Monthly mortgage repayment (AUD)
                            <input
                                type="number"
                                value={userInputs.monthlyMortgage}
                                onChange={(e) => setUserInputs((prev) => ({ ...prev, monthlyMortgage: e.target.value }))}
                            />
                            <small className="hint">Normal range: {rangeLabel('monthly_mortgage')}</small>
                        </label>

                        <label>
                            Mortgage burden target (% of household income)
                            <input
                                type="number"
                                step="0.1"
                                min="5"
                                max="80"
                                value={userInputs.mortgageBurdenPct}
                                onChange={(e) => setUserInputs((prev) => ({ ...prev, mortgageBurdenPct: e.target.value }))}
                            />
                            <small className="hint">Normal range: {rangeLabel('mortgage_burden_pct', 1, '%')}</small>
                        </label>

                        <label>
                            Weekly rent expectation (AUD)
                            <input
                                type="number"
                                value={userInputs.weeklyRent}
                                onChange={(e) => setUserInputs((prev) => ({ ...prev, weeklyRent: e.target.value }))}
                            />
                            <small className="hint">Normal range: {rangeLabel('weekly_rent')}</small>
                        </label>

                        <label>
                            SEIFA score (socio-economic resilience)
                            <input
                                type="number"
                                value={userInputs.seifaScore}
                                onChange={(e) => setUserInputs((prev) => ({ ...prev, seifaScore: e.target.value }))}
                            />
                            <small className="hint">Normal range: {rangeLabel('seifa_score')}</small>
                        </label>

                        <label>
                            Population size
                            <input
                                type="number"
                                value={userInputs.population}
                                onChange={(e) => setUserInputs((prev) => ({ ...prev, population: e.target.value }))}
                            />
                            <small className="hint">Normal range: {rangeLabel('population_size')}</small>
                        </label>

                        <label>
                            Median age (years)
                            <input
                                type="number"
                                value={userInputs.medianAge}
                                onChange={(e) => setUserInputs((prev) => ({ ...prev, medianAge: e.target.value }))}
                            />
                            <small className="hint">Normal range: {rangeLabel('median_age_years')}</small>
                        </label>

                        <label>
                            Average household size
                            <input
                                type="number"
                                step="0.1"
                                value={userInputs.householdSize}
                                onChange={(e) => setUserInputs((prev) => ({ ...prev, householdSize: e.target.value }))}
                            />
                            <small className="hint">Normal range: {rangeLabel('household_size', 1)}</small>
                        </label>

                        <label>
                            Working-age residents (%)
                            <input
                                type="number"
                                step="0.1"
                                min="0"
                                max="100"
                                value={userInputs.workingAgePct}
                                onChange={(e) => setUserInputs((prev) => ({ ...prev, workingAgePct: e.target.value }))}
                            />
                            <small className="hint">Normal range: {rangeLabel('working_age_pct', 1, '%')}</small>
                        </label>

                        <label>
                            Senior residents (%)
                            <input
                                type="number"
                                step="0.1"
                                min="0"
                                max="100"
                                value={userInputs.seniorPct}
                                onChange={(e) => setUserInputs((prev) => ({ ...prev, seniorPct: e.target.value }))}
                            />
                            <small className="hint">Normal range: {rangeLabel('senior_pct', 1, '%')}</small>
                        </label>

                        <label>
                            Residents from diverse backgrounds (%)
                            <input
                                type="number"
                                step="0.1"
                                min="0"
                                max="100"
                                value={userInputs.diversityPct}
                                onChange={(e) => setUserInputs((prev) => ({ ...prev, diversityPct: e.target.value }))}
                            />
                            <small className="hint">Normal range: {rangeLabel('diversity_pct', 1, '%')}</small>
                        </label>
                    </div>

                    <button className="submit" type="submit" disabled={loading || Object.keys(modelDefaults).length === 0}>
                        {loading ? 'Running prediction...' : 'Run Prediction'}
                    </button>
                </form>

                {error ? <p className="error">{error}</p> : null}
            </section>

            {prediction ? (
                <section className="card results">
                    <h2>Prediction Result</h2>
                    <div className="prediction-metrics">
                        <p>
                            <span>Predicted ROI</span>
                            <strong>{prediction.predicted_roi_percent}%</strong>
                        </p>
                        <p>
                            <span>Percentile</span>
                            <strong>{prediction.percentile_vs_all_suburbs}%</strong>
                        </p>
                        <p>
                            <span>Signal</span>
                            <strong>{prediction.investment_signal}</strong>
                        </p>
                    </div>

                    <h3>5 Suburbs With ROI Closest To Your Prediction</h3>
                    <div className="opportunity-grid">
                        {opportunities.map((opportunity) => (
                            <article className="opportunity-card" key={opportunity.name}>
                                <h4>{opportunity.name}</h4>
                                <p>ROI: {roiPercent(opportunity.roi)}</p>
                                <p>Gap vs prediction: {roiPercent(opportunity.roi_diff)}</p>
                                <p>Mortgage: ${Number(opportunity.price || 0).toLocaleString()}</p>
                                <p>Rent: ${Number(opportunity.rent || 0).toLocaleString()}</p>
                            </article>
                        ))}
                    </div>
                </section>
            ) : null}
        </main>
    )
}

export default App
