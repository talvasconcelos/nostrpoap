function loadTemplateAsync(path) {
  const result = new Promise(resolve => {
    const xhttp = new XMLHttpRequest()

    xhttp.onreadystatechange = function () {
      if (this.readyState == 4) {
        if (this.status == 200) resolve(this.responseText)

        if (this.status == 404) resolve(`<div>Page not found: ${path}</div>`)
      }
    }

    xhttp.open('GET', path, true)
    xhttp.send()
  })

  return result
}

function mapPoaps(obj) {
  obj.date = Quasar.utils.date.formatDate(
    new Date(obj.event_created_at * 1000),
    'YYYY-MM-DD HH:mm'
  )
  obj.dateFrom = moment(obj.date).fromNow()
  if (obj?.geohash) {
    const [lat, long] = gh_decode(obj.geohash)
    obj.lat = lat
    obj.long = long
  }
  return obj
}

function satOrBtc(val, showUnit = true, showSats = false) {
  const value = showSats
    ? LNbits.utils.formatSat(val)
    : val == 0
    ? 0.0
    : (val / 100000000).toFixed(8)
  if (!showUnit) return value
  return showSats ? value + ' sat' : value + ' BTC'
}

function isValidKey(key, prefix = 'n') {
  try {
    if (key && key.startsWith(prefix)) {
      let {_, data} = NostrTools.nip19.decode(key)
      key = data
    }
    return isValidKeyHex(key)
  } catch (error) {
    return false
  }
}

function isValidKeyHex(key) {
  return key?.toLowerCase()?.match(/^[0-9a-f]{64}$/)
}

function formatCurrency(value, currency) {
  return new Intl.NumberFormat(window.LOCALE, {
    style: 'currency',
    currency: currency
  }).format(value)
}

/////////////////////// Geohash ///////////////////////
const base32 = '0123456789bcdefghjkmnpqrstuvwxyz'
const decodeMap = {}
for (let i = 0; i < base32.length; i++) {
  decodeMap[base32[i]] = i
}

function decodeExactly(geohash) {
  let latInterval = [-90.0, 90.0]
  let lonInterval = [-180.0, 180.0]
  let latErr = 90.0
  let lonErr = 180.0
  let isEven = true

  for (const c of geohash) {
    const cd = decodeMap[c]
    for (const mask of [16, 8, 4, 2, 1]) {
      if (isEven) {
        // adds longitude info
        lonErr /= 2
        if (cd & mask) {
          lonInterval = [(lonInterval[0] + lonInterval[1]) / 2, lonInterval[1]]
        } else {
          lonInterval = [lonInterval[0], (lonInterval[0] + lonInterval[1]) / 2]
        }
      } else {
        // adds latitude info
        latErr /= 2
        if (cd & mask) {
          latInterval = [(latInterval[0] + latInterval[1]) / 2, latInterval[1]]
        } else {
          latInterval = [latInterval[0], (latInterval[0] + latInterval[1]) / 2]
        }
      }
      isEven = !isEven
    }
  }

  const lat = (latInterval[0] + latInterval[1]) / 2
  const lon = (lonInterval[0] + lonInterval[1]) / 2
  return [lat, lon, latErr, lonErr]
}

function gh_decode(geohash) {
  const [lat, lon, latErr, lonErr] = decodeExactly(geohash)

  // Format to the number of decimals that are known
  const lats = lat
    .toFixed(Math.max(1, Math.round(-Math.log10(latErr))) - 1)
    .replace(/\.?0+$/, '')
  const lons = lon
    .toFixed(Math.max(1, Math.round(-Math.log10(lonErr))) - 1)
    .replace(/\.?0+$/, '')

  return [parseFloat(lats), parseFloat(lons)]
}

function gh_encode(latitude, longitude, precision = 12) {
  let latInterval = [-90.0, 90.0]
  let lonInterval = [-180.0, 180.0]
  const geohash = []
  const bits = [16, 8, 4, 2, 1]
  let bit = 0
  let ch = 0
  let even = true

  while (geohash.length < precision) {
    if (even) {
      const mid = (lonInterval[0] + lonInterval[1]) / 2
      if (longitude > mid) {
        ch |= bits[bit]
        lonInterval = [mid, lonInterval[1]]
      } else {
        lonInterval = [lonInterval[0], mid]
      }
    } else {
      const mid = (latInterval[0] + latInterval[1]) / 2
      if (latitude > mid) {
        ch |= bits[bit]
        latInterval = [mid, latInterval[1]]
      } else {
        latInterval = [latInterval[0], mid]
      }
    }
    even = !even
    if (bit < 4) {
      bit += 1
    } else {
      geohash.push(base32[ch])
      bit = 0
      ch = 0
    }
  }

  return geohash.join('')
}
