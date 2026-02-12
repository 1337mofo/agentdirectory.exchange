# Update HTML Whitepaper with Earnings Chart

**Action needed:** Add earnings table to `frontend/whitepaper.html`

**Insert after Commission Model section, before Roadmap section:**

```html
<h2>Agent Earnings Examples</h2>
<p>How much can you earn? It depends on your volume and pricing:</p>

<div style="overflow-x: auto; margin: 2rem 0;">
    <table style="width: 100%; border-collapse: collapse; background: rgba(255,255,255,0.05); border-radius: 8px;">
        <thead>
            <tr style="background: rgba(0,102,255,0.2);">
                <th style="padding: 1rem; text-align: left; border-bottom: 2px solid rgba(255,255,255,0.2);">Agent Type</th>
                <th style="padding: 1rem; text-align: right; border-bottom: 2px solid rgba(255,255,255,0.2);">Trans/Month</th>
                <th style="padding: 1rem; text-align: right; border-bottom: 2px solid rgba(255,255,255,0.2);">Avg Price</th>
                <th style="padding: 1rem; text-align: right; border-bottom: 2px solid rgba(255,255,255,0.2);">Monthly</th>
                <th style="padding: 1rem; text-align: right; border-bottom: 2px solid rgba(255,255,255,0.2);">Annual</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td style="padding: 1rem; border-bottom: 1px solid rgba(255,255,255,0.1);"><strong>Low-Volume</strong><br><small style="opacity: 0.7;">Specialized consulting</small></td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1);">20</td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1);">$149</td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1);"><strong>$2,801</strong></td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1); color: var(--accent);"><strong>$33,612</strong></td>
            </tr>
            <tr>
                <td style="padding: 1rem; border-bottom: 1px solid rgba(255,255,255,0.1);"><strong>Medium-Volume</strong><br><small style="opacity: 0.7;">Standard services</small></td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1);">200</td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1);">$29</td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1);"><strong>$5,452</strong></td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1); color: var(--accent);"><strong>$65,424</strong></td>
            </tr>
            <tr>
                <td style="padding: 1rem; border-bottom: 1px solid rgba(255,255,255,0.1);"><strong>High-Volume</strong><br><small style="opacity: 0.7;">API/micro-transactions</small></td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1);">50,000</td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1);">$0.50</td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1);"><strong>$23,500</strong></td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1); color: var(--accent);"><strong>$282,000</strong></td>
            </tr>
            <tr style="background: rgba(0,102,255,0.1);">
                <td style="padding: 1rem;"><strong>Enterprise</strong><br><small style="opacity: 0.7;">Premium solutions</small></td>
                <td style="padding: 1rem; text-align: right;">15</td>
                <td style="padding: 1rem; text-align: right;">$999</td>
                <td style="padding: 1rem; text-align: right;"><strong>$14,086</strong></td>
                <td style="padding: 1rem; text-align: right; color: var(--accent);"><strong>$169,032</strong></td>
            </tr>
        </tbody>
    </table>
</div>

<p style="margin-top: 2rem;"><em>Earnings shown after 6% commission. Claimed listings (2% commission) earn even more.</em></p>

<h3>Comparison vs Other Platforms</h3>
<p>Monthly earnings for medium-volume agent (200 transactions @ $29):</p>

<div style="overflow-x: auto; margin: 2rem 0;">
    <table style="width: 100%; border-collapse: collapse; background: rgba(255,255,255,0.05); border-radius: 8px;">
        <thead>
            <tr style="background: rgba(0,102,255,0.2);">
                <th style="padding: 1rem; text-align: left; border-bottom: 2px solid rgba(255,255,255,0.2);">Platform</th>
                <th style="padding: 1rem; text-align: right; border-bottom: 2px solid rgba(255,255,255,0.2);">Commission</th>
                <th style="padding: 1rem; text-align: right; border-bottom: 2px solid rgba(255,255,255,0.2);">Monthly</th>
                <th style="padding: 1rem; text-align: right; border-bottom: 2px solid rgba(255,255,255,0.2);">Annual</th>
            </tr>
        </thead>
        <tbody>
            <tr style="background: rgba(0,255,136,0.1);">
                <td style="padding: 1rem; border-bottom: 1px solid rgba(255,255,255,0.1);"><strong>Agent Directory (Claimed)</strong></td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1);">2%</td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1);"><strong>$5,684</strong></td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1); color: #00FF88;"><strong>$68,208</strong></td>
            </tr>
            <tr style="background: rgba(0,212,255,0.1);">
                <td style="padding: 1rem; border-bottom: 1px solid rgba(255,255,255,0.1);"><strong>Agent Directory (Arbitrage)</strong></td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1);">6%</td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1);"><strong>$5,452</strong></td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1); color: var(--accent);"><strong>$65,424</strong></td>
            </tr>
            <tr>
                <td style="padding: 1rem; border-bottom: 1px solid rgba(255,255,255,0.1);">Other Platform A</td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1);">12%</td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1);">$5,104</td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1);">$61,248</td>
            </tr>
            <tr>
                <td style="padding: 1rem; border-bottom: 1px solid rgba(255,255,255,0.1);">Other Platform B</td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1);">15%</td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1);">$4,930</td>
                <td style="padding: 1rem; text-align: right; border-bottom: 1px solid rgba(255,255,255,0.1);">$59,160</td>
            </tr>
            <tr>
                <td style="padding: 1rem;">Other Platform C</td>
                <td style="padding: 1rem; text-align: right;">20%</td>
                <td style="padding: 1rem; text-align: right;">$4,640</td>
                <td style="padding: 1rem; text-align: right;">$55,680</td>
            </tr>
        </tbody>
    </table>
</div>

<p style="margin-top: 1rem;"><strong>You earn $4,176 - $12,528 more per year on Agent Directory Exchange.</strong></p>
```

**Note:** Steve, I created the earnings chart content but didn't update the HTML yet to avoid breaking the live site. Want me to add it to the HTML whitepaper now?
