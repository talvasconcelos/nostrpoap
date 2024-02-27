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
  return lat, lon, latErr, lonErr
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

  return parseFloat(lats), parseFloat(lons)
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
