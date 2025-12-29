# Portfolio Summary Template

Use this template to format the portfolio optimization results for the user.

## Portfolio Header

**Title:** Your Optimized Shariah Portfolio

**Investment Amount:** {{investment_amount}} EGP

## Allocation Table

| Ticker | Company | Weight | Amount (EGP) |
|--------|---------|--------|--------------|
{{allocation_rows}}

## Metrics Section

### Expected Return: {{expected_return}}%

> This is the predicted annual return based on our AI model's analysis of historical patterns. If this holds, a {{investment_amount}} EGP investment could grow to approximately {{projected_value}} EGP over one year.

### Expected Volatility: {{volatility}}% ({{risk_level}} Risk)

> Volatility measures how much the portfolio value may fluctuate. This portfolio is {{risk_description}}. Expect daily swings of roughly {{daily_swing}}% on average.

### Sharpe Ratio: {{sharpe_ratio}}

> The Sharpe Ratio measures return per unit of risk. Higher is better (above 1.0 is excellent). {{sharpe_interpretation}}

## Risk Level Interpretations

Use these based on volatility percentage:

- **Low Risk** (volatility < 15%): "relatively stable with smaller price swings"
- **Moderate Risk** (15% ≤ volatility < 25%): "balanced between stability and growth potential"
- **High Risk** (volatility ≥ 25%): "more volatile but with higher growth potential"

## Sharpe Ratio Interpretations

- **Below 0.5**: "The risk-adjusted return is below average. Consider a more conservative allocation."
- **0.5 to 1.0**: "The portfolio offers reasonable risk-adjusted returns."
- **Above 1.0**: "Excellent risk-adjusted returns - the portfolio is well-optimized."

## Footer

---

*This portfolio is optimized using AI-powered predictions and Mean-Variance Optimization, focusing on Shariah-compliant EGX stocks. Past performance does not guarantee future results.*

## Follow-up Prompt

Would you like me to adjust anything or create a different portfolio?