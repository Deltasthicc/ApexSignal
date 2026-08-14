$ErrorActionPreference = "Stop"

function Get-JsonWithRetry([string]$Uri) {
  for ($attempt = 1; $attempt -le 4; $attempt++) {
    try {
      return Invoke-RestMethod -Uri $Uri -TimeoutSec 45
    } catch {
      if ($attempt -eq 4) { throw }
      Start-Sleep -Seconds ([Math]::Pow(2, $attempt))
    }
  }
}

function ConvertTo-Seconds([string]$LapTime) {
  # Ergast/Jolpica lap times are "M:SS.sss" -- the driver's own time to
  # complete that specific lap, not a gap or time-of-day. Used to build a
  # real cumulative race clock per driver, not assumed/uniform spacing.
  $parts = $LapTime -split ':'
  return ([double]$parts[0] * 60.0) + [double]$parts[1]
}

function Get-AllLapRows([string]$Base) {
  $rowsByLap = [ordered]@{}
  $offset = 0
  $total = 1
  while ($offset -lt $total) {
    $payload = Get-JsonWithRetry "$Base/laps.json?limit=100&offset=$offset"
    $total = [int]$payload.MRData.total
    foreach ($lap in @($payload.MRData.RaceTable.Races[0].Laps)) {
      $lapNumber = [string]$lap.number
      if (-not $rowsByLap.Contains($lapNumber)) {
        $rowsByLap[$lapNumber] = [System.Collections.Generic.List[object]]::new()
      }
      foreach ($timing in @($lap.Timings)) {
        if (-not ($rowsByLap[$lapNumber] | Where-Object driverId -eq $timing.driverId)) {
          $rowsByLap[$lapNumber].Add($timing)
        }
      }
    }
    $offset += 100
  }
  return @($rowsByLap.GetEnumerator() | Sort-Object { [int]$_.Key } | ForEach-Object {
    [pscustomobject]@{ number = $_.Key; Timings = @($_.Value) }
  })
}

$races = @(
  @{ circuitKey = "Melbourne"; season = 2010; round = 2; note = "Button wins a wet-dry Albert Park classic" },
  @{ circuitKey = "Spa"; season = 1998; round = 13; note = "Hill wins after the famous chaotic start" },
  @{ circuitKey = "Monza"; season = 2020; round = 8; note = "Gasly takes a landmark maiden victory" },
  @{ circuitKey = "Silverstone"; season = 2021; round = 10; note = "Hamilton wins a dramatic British Grand Prix" },
  @{ circuitKey = "Suzuka"; season = 2005; round = 18; note = "Raikkonen charges from 17th to victory" },
  @{ circuitKey = "SaoPaulo"; season = 2008; round = 18; note = "The championship turns on the final corner" },
  @{ circuitKey = "Sakhir"; season = 2014; round = 3; note = "The Mercedes duel remembered as the Duel in the Desert" },
  @{ circuitKey = "Austin"; season = 2018; round = 18; note = "Raikkonen ends a five-year wait for victory" },
  @{ circuitKey = "Catalunya"; season = 2016; round = 5; note = "Verstappen becomes Formula 1's youngest winner" },
  @{ circuitKey = "Spielberg"; season = 2019; round = 9; note = "Verstappen and Leclerc fight for the win" },
  @{ circuitKey = "Zandvoort"; season = 2021; round = 13; note = "The Dutch Grand Prix returns after 36 years" },
  @{ circuitKey = "Montreal"; season = 2011; round = 7; note = "Button wins Formula 1's longest race" },
  @{ circuitKey = "MexicoCity"; season = 2021; round = 18; note = "Verstappen controls the race from Turn 1" },
  @{ circuitKey = "Hungaroring"; season = 2021; round = 11; note = "Ocon survives the chaos for his maiden win" },
  @{ circuitKey = "Shanghai"; season = 2018; round = 3; note = "Ricciardo's late-braking charge wins in China" },
  @{ circuitKey = "YasMarina"; season = 2021; round = 22; note = "The world championship is decided on the final lap" },
  @{ circuitKey = "Sepang"; season = 2012; round = 2; note = "Alonso holds off Perez in changing conditions" },
  @{ circuitKey = "Hockenheim"; season = 2019; round = 11; note = "Rain produces a modern German Grand Prix classic" },
  @{ circuitKey = "Nuerburgring"; season = 2020; round = 11; note = "Hamilton equals Schumacher's 91-win record" },
  @{ circuitKey = "Sochi"; season = 2021; round = 15; note = "Late rain overturns the Russian Grand Prix" },
  @{ circuitKey = "IMS"; season = 2005; round = 9; note = "Twenty qualify; six start after the Michelin withdrawal" }
)

$teamColors = @{
  mercedes = "#00d2be"; ferrari = "#dc0000"; red_bull = "#1e41ff";
  mclaren = "#ff8700"; renault = "#fff500"; alpine = "#2293d1";
  aston_martin = "#006f62"; racing_point = "#f596c8"; force_india = "#f596c8";
  alphatauri = "#2b4562"; toro_rosso = "#469bff"; sauber = "#9b0000";
  alfa = "#900000"; williams = "#005aff"; haas = "#ffffff";
  lotus_f1 = "#b6babd"; toyota = "#cc0000"; honda = "#ffffff";
  jordan = "#f9dc16"; bar = "#ffffff"; minardi = "#1f4ba5";
  jaguar = "#0b5f20"; bmw_sauber = "#ffffff"; super_aguri = "#e51b23";
  mf1 = "#ff9a00"; spyker_mf1 = "#ff6600"; brawn = "#b8ff00";
  virgin = "#c82e37"; hrt = "#777777"; caterham = "#006b33";
  marussia = "#6e0000"; lotus_racing = "#006b33"; prost = "#0046ad";
  arrows = "#ff7b00"; benetton = "#00a84f"; stewart = "#ffffff";
  tyrrell = "#003399"; ligier = "#001f8c"; forti = "#f7e800";
  arrows_footwork = "#ffffff"; pacific = "#003399"; simtek = "#5b2c83";
  alpha_tauri = "#2b4562"; rb = "#6692ff"; kick_sauber = "#52e252"
}

$output = @()
foreach ($raceSpec in $races) {
  $base = "https://api.jolpi.ca/ergast/f1/$($raceSpec.season)/$($raceSpec.round)"
  Write-Host "Downloading $($raceSpec.circuitKey) $($raceSpec.season)..."
  $resultPayload = Get-JsonWithRetry "$base/results.json"
  $race = $resultPayload.MRData.RaceTable.Races[0]
  $lapRows = @(Get-AllLapRows $base)
  $resultRows = @($race.Results)

  $drivers = foreach ($result in $resultRows) {
    $constructorId = [string]$result.Constructor.constructorId
    $color = $teamColors[$constructorId]
    if (-not $color) { $color = "#d0d0d0" }
    [ordered]@{
      id = [string]$result.Driver.driverId
      code = if ($result.Driver.code) { [string]$result.Driver.code } else { ([string]$result.Driver.familyName).Substring(0, [Math]::Min(3, ([string]$result.Driver.familyName).Length)).ToUpperInvariant() }
      number = [string]$result.number
      name = "$($result.Driver.givenName) $($result.Driver.familyName)"
      team = [string]$result.Constructor.name
      teamId = $constructorId
      color = $color
      grid = [int]$result.grid
      finish = [int]$result.position
      lapsCompleted = [int]$result.laps
      status = [string]$result.status
    }
  }

  $gridOrder = @($drivers | Sort-Object @{ Expression = { if ($_.grid -eq 0) { 999 } else { $_.grid } } } | ForEach-Object { $_.id })
  $orders = [System.Collections.Generic.List[object]]::new()
  $orders.Add(@($gridOrder))

  # Real per-driver cumulative race time, accumulated lap by lap from each
  # driver's own recorded lap time -- not a stand-in for track position.
  # gaps[lapIndex] is a lap-time gap-to-leader in SECONDS, parallel to
  # orders[lapIndex] (same driver, same array position). The frontend
  # divides by avgLapTimeS to turn that into a fraction of the track loop,
  # instead of the previous fixed "position * constant" spacing that had
  # no relationship to how far apart the real cars actually were.
  $cumulative = @{}
  foreach ($driver in $drivers) { $cumulative[$driver.id] = 0.0 }
  $gaps = [System.Collections.Generic.List[object]]::new()
  $gaps.Add(@($gridOrder | ForEach-Object { 0.0 }))

  foreach ($lap in $lapRows) {
    foreach ($timing in $lap.Timings) {
      $cumulative[[string]$timing.driverId] += ConvertTo-Seconds ([string]$timing.time)
    }
    $orderedIds = @($lap.Timings | Sort-Object { [int]$_.position } | ForEach-Object { [string]$_.driverId })
    $orders.Add($orderedIds)
    $leaderTime = $cumulative[$orderedIds[0]]
    $gaps.Add(@($orderedIds | ForEach-Object { [Math]::Round(($cumulative[$_] - $leaderTime), 3) }))
  }

  $raceDistance = [int](($resultRows | Measure-Object -Property laps -Maximum).Maximum)
  if ($orders.Count -ne ($raceDistance + 1)) {
    throw "$($raceSpec.circuitKey) timing coverage is incomplete: expected $raceDistance laps, reconstructed $($orders.Count - 1)."
  }

  $winnerId = $orders[$orders.Count - 1][0]
  $avgLapTimeS = [Math]::Round($cumulative[$winnerId] / $raceDistance, 3)

  $output += [ordered]@{
    circuitKey = $raceSpec.circuitKey
    season = [int]$race.season
    round = [int]$race.round
    eventName = [string]$race.raceName
    date = [string]$race.date
    totalLaps = $raceDistance
    note = $raceSpec.note
    sourceUrl = $base
    articleUrl = [string]$race.url
    avgLapTimeS = $avgLapTimeS
    drivers = @($drivers)
    orders = @($orders)
    gaps = @($gaps)
  }
}

$json = $output | ConvertTo-Json -Depth 8 -Compress
$target = Join-Path $PSScriptRoot "..\apps\web\src\data\raceReplays.json"
[System.IO.File]::WriteAllText((Resolve-Path (Split-Path $target)).Path + "\raceReplays.json", $json, [System.Text.UTF8Encoding]::new($false))
Write-Host "Wrote $target"
