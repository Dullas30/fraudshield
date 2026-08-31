Add-Type -AssemblyName System.Drawing

$w = 1600
$h = 1200
$out = Join-Path (Get-Location) "fraudshield_mockup_v2.png"

$bmp = New-Object System.Drawing.Bitmap $w, $h
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit

function New-Brush($r, $g, $b, $a = 255) {
  New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb($a, $r, $g, $b))
}

function Draw-RoundedRect($x, $y, $rw, $rh, $radius, $fill, $stroke) {
  $path = New-Object System.Drawing.Drawing2D.GraphicsPath
  $d = $radius * 2
  $path.AddArc($x, $y, $d, $d, 180, 90)
  $path.AddArc($x + $rw - $d, $y, $d, $d, 270, 90)
  $path.AddArc($x + $rw - $d, $y + $rh - $d, $d, $d, 0, 90)
  $path.AddArc($x, $y + $rh - $d, $d, $d, 90, 90)
  $path.CloseFigure()
  $g.FillPath($fill, $path)
  $g.DrawPath($stroke, $path)
  $path.Dispose()
}

function Draw-Card($x, $y, $rw, $rh) {
  $fill = New-Brush 9 16 31 238
  $stroke = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(170, 33, 51, 82), 1.2)
  Draw-RoundedRect $x $y $rw $rh 20 $fill $stroke
  $fill.Dispose()
  $stroke.Dispose()
}

function Draw-Metric($x, $y, $label, $value, $sub, $color) {
  Draw-Card $x $y 320 106
  $g.DrawString($label, (New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)), (New-Brush 154 171 196), $x + 16, $y + 14)
  $valBrush = New-Brush $color[0] $color[1] $color[2]
  $g.DrawString($value, (New-Object System.Drawing.Font("Segoe UI Semibold", 28, [System.Drawing.FontStyle]::Bold)), $valBrush, $x + 16, $y + 34)
  $valBrush.Dispose()
  $g.DrawString($sub, (New-Object System.Drawing.Font("Segoe UI", 9)), (New-Brush 154 171 196), $x + 16, $y + 76)
}

function Draw-Scenario($x, $y, $w2, $title, $tag, $tagColor, $desc) {
  Draw-Card $x $y $w2 120
  $g.DrawString($title, (New-Object System.Drawing.Font("Segoe UI", 15, [System.Drawing.FontStyle]::Bold)), [System.Drawing.Brushes]::White, $x + 16, $y + 14)
  $tagBrush = New-Brush $tagColor[0] $tagColor[1] $tagColor[2]
  $g.DrawString($tag, (New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)), $tagBrush, $x + $w2 - 84, $y + 18)
  $tagBrush.Dispose()
  $g.DrawString($desc, (New-Object System.Drawing.Font("Segoe UI", 10)), (New-Brush 154 171 196), $x + 16, $y + 54)
}

function Draw-Feed($x, $y, $id, $loc, $amt, $score, $scoreColor) {
  Draw-Card $x $y 434 76
  $g.DrawString($id, (New-Object System.Drawing.Font("Consolas", 14, [System.Drawing.FontStyle]::Bold)), [System.Drawing.Brushes]::White, $x + 14, $y + 12)
  $g.DrawString($loc, (New-Object System.Drawing.Font("Segoe UI", 10)), (New-Brush 154 171 196), $x + 14, $y + 40)
  $g.DrawString($amt, (New-Object System.Drawing.Font("Consolas", 12)), (New-Brush 190 237 255), $x + 230, $y + 14)
  $scoreBrush = New-Brush $scoreColor[0] $scoreColor[1] $scoreColor[2]
  $g.DrawString($score, (New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Bold)), $scoreBrush, $x + 330, $y + 23)
  $scoreBrush.Dispose()
}

$bg = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
  [System.Drawing.Rectangle]::new(0, 0, $w, $h),
  ([System.Drawing.Color]::FromArgb(255, 7, 17, 31)),
  ([System.Drawing.Color]::FromArgb(255, 11, 20, 36)),
  90
)
$g.FillRectangle($bg, 0, 0, $w, $h)
$bg.Dispose()

$g.FillEllipse((New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(35, 57, 197, 255))), -70, -30, 520, 320)
$g.FillEllipse((New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(28, 141, 140, 255))), 1160, 20, 360, 260)

Draw-Card 30 26 1540 74
$logoBrush = New-Brush 0 212 255
$g.FillEllipse($logoBrush, 52, 44, 40, 40)
$logoBrush.Dispose()
$g.DrawString("F", (New-Object System.Drawing.Font("Segoe UI", 19, [System.Drawing.FontStyle]::Bold)), (New-Brush 8 17 31), 64, 49)
$g.DrawString("FraudShield", (New-Object System.Drawing.Font("Segoe UI Semibold", 24, [System.Drawing.FontStyle]::Bold)), [System.Drawing.Brushes]::White, 108, 39)
$g.DrawString("Real-time electricity payment fraud detection", (New-Object System.Drawing.Font("Segoe UI", 10)), (New-Brush 154 171 196), 110, 71)
$liveDot = New-Brush 46 208 107
$g.FillEllipse($liveDot, 1340, 50, 10, 10)
$liveDot.Dispose()
$g.DrawString("LIVE INFERENCE", (New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)), (New-Brush 137 239 173), 1360, 43)

Draw-Card 30 122 1040 310
$banner = New-Brush 57 197 255 28
$g.FillRectangle($banner, 54, 148, 192, 28)
$banner.Dispose()
$g.DrawString("FRAUD ANALYTICS DASHBOARD", (New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)), (New-Brush 190 237 255), 66, 154)
$g.DrawString("Catch suspicious transactions before they clear.", (New-Object System.Drawing.Font("Segoe UI Semibold", 34, [System.Drawing.FontStyle]::Bold)), [System.Drawing.Brushes]::White, 54, 188)
$g.DrawString("A clean command-center view for payment monitoring, combining model confidence, risk scoring, and live transaction activity in one screen designed for demos and stakeholder presentations.", (New-Object System.Drawing.Font("Segoe UI", 13)), (New-Brush 154 171 196), 56, 244)

Draw-Metric 54 322 "Model accuracy" "96.4%" "Measured on the test split" @(46,208,107)
Draw-Metric 388 322 "Avg. latency" "48ms" "Fast enough for live review" @(141,140,255)
Draw-Metric 722 322 "Fraud blocked" "NGN 8.7M" "Estimated on the test split" @(244,176,74)

Draw-Card 1092 122 478 310
$g.DrawString("CURRENT RISK POSTURE", (New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)), (New-Brush 154 171 196), 1114, 145)
$g.DrawString("Updated live", (New-Object System.Drawing.Font("Segoe UI", 10)), (New-Brush 154 171 196), 1470, 145)
Draw-RoundedRect 1240 175 180 180 90 (New-Brush 11 20 36) (New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(255, 46, 208, 107), 1.6))
$g.DrawString("0.93", (New-Object System.Drawing.Font("Segoe UI Semibold", 40, [System.Drawing.FontStyle]::Bold)), [System.Drawing.Brushes]::White, 1282, 228)
$g.DrawString("fraud score", (New-Object System.Drawing.Font("Segoe UI", 10)), (New-Brush 154 171 196), 1284, 277)
Draw-Card 1122 370 438 46
$alertBrush = New-Brush 255 154 162
$g.DrawString("High confidence alert", (New-Object System.Drawing.Font("Segoe UI", 13, [System.Drawing.FontStyle]::Bold)), $alertBrush, 1138, 381)
$alertBrush.Dispose()
$g.DrawString("SIM swap, VPN, and unusual time pattern", (New-Object System.Drawing.Font("Segoe UI", 10)), (New-Brush 154 171 196), 1138, 405)
$amtBrush = New-Brush 190 237 255
$g.DrawString("NGN 250,000", (New-Object System.Drawing.Font("Consolas", 12)), $amtBrush, 1456, 385)
$amtBrush.Dispose()

Draw-Card 30 456 1040 350
Draw-Card 1092 456 478 350
$g.DrawString("EXAMPLE SCENARIOS", (New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)), (New-Brush 154 171 196), 54, 478)
$g.DrawString("Click-through demo states", (New-Object System.Drawing.Font("Segoe UI", 10)), (New-Brush 154 171 196), 236, 480)
$g.DrawString("LIVE FEED", (New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)), (New-Brush 154 171 196), 1116, 478)
$g.DrawString("Streaming events", (New-Object System.Drawing.Font("Segoe UI", 10)), (New-Brush 154 171 196), 1228, 480)

Draw-Scenario 54 512 492 "SIM Swap Attack" "HIGH" @(255,154,162) "Recent SIM swap + VPN + 3AM + NGN 250,000 + new device"
Draw-Scenario 566 512 492 "Rapid-Fire Payments" "HIGH" @(255,154,162) "15 transactions/hr - 8 meter IDs - new account (12 days)"
Draw-Scenario 54 642 492 "Account Takeover" "MEDIUM" @(255,212,141) "5 failed logins + new device + distant location + VPN"
Draw-Scenario 566 642 492 "Legitimate Payment" "LOW" @(158,240,185) "Regular customer - 2PM - known device - NGN 5,000 top-up"

Draw-Feed 1116 512 "TXN1048821" "Lagos - mobile_app" "NGN 250,000" "98.1% HIGH" @(255,100,112)
Draw-Feed 1116 600 "TXN1048822" "Abuja - ussd" "NGN 8,500" "7.4% LOW" @(158,240,185)
Draw-Feed 1116 688 "TXN1048823" "Rivers - web" "NGN 46,000" "63.2% MEDIUM" @(255,212,141)

Draw-Card 30 826 1000 330
Draw-Card 1050 826 520 330
$g.DrawString("MODEL COMPARISON", (New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)), (New-Brush 154 171 196), 54, 848)
$g.DrawString("Visualized confidence", (New-Object System.Drawing.Font("Segoe UI", 10)), (New-Brush 154 171 196), 212, 850)
$g.DrawString("PRESENTATION ANGLE", (New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)), (New-Brush 154 171 196), 1072, 848)
$g.DrawString("What to say", (New-Object System.Drawing.Font("Segoe UI", 10)), (New-Brush 154 171 196), 1198, 850)

Draw-Card 54 888 920 218
$barColors = @(
  @(57,197,255),
  @(46,208,107),
  @(141,140,255),
  @(255,100,112),
  @(244,176,74)
)
$heights = @(64, 132, 92, 182, 116)
for ($i = 0; $i -lt 5; $i++) {
  $x = 96 + ($i * 160)
  $c = $barColors[$i]
  $grad = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
    [System.Drawing.Rectangle]::new($x, 1070 - $heights[$i], 86, $heights[$i]),
    [System.Drawing.Color]::FromArgb(255, $c[0], $c[1], $c[2]),
    [System.Drawing.Color]::FromArgb(55, $c[0], $c[1], $c[2]),
    90
  )
  $g.FillRectangle($grad, $x, 1070 - $heights[$i], 86, $heights[$i])
  $grad.Dispose()
}

$g.DrawString("This dashboard combines explainable risk signals with live monitoring.", (New-Object System.Drawing.Font("Segoe UI", 10)), [System.Drawing.Brushes]::White, 1074, 892)
$g.DrawString("It feels polished because the top row gives executives quick proof, while the center panels show how the system reacts to suspicious behavior in practice.", (New-Object System.Drawing.Font("Segoe UI", 10)), (New-Brush 154 171 196), 1074, 922)
$g.DrawString("1. Lead with the top metrics.", (New-Object System.Drawing.Font("Segoe UI", 10)), [System.Drawing.Brushes]::White, 1074, 1010)
$g.DrawString("2. Show a scenario click.", (New-Object System.Drawing.Font("Segoe UI", 10)), [System.Drawing.Brushes]::White, 1074, 1038)
$g.DrawString("3. End with the live feed and fraud score.", (New-Object System.Drawing.Font("Segoe UI", 10)), [System.Drawing.Brushes]::White, 1074, 1066)

$g.Dispose()
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()

Write-Output $out
