const issuer = async () => {
  Vue.component(VueQrcode.name, VueQrcode)

  await keyPair('static/components/key-pair/key-pair.html')
  await issuerDetails('static/components/issuer-details/issuer-details.html')
  await poapList('static/components/poap-list/poap-list.html')
  await awardsTable('static/components/awards-table/awards-table.html')

  const nostr = window.NostrTools

  new Vue({
    el: '#vue',
    mixins: [windowMixin],
    delimiters: ['${', '}'],
    data: function () {
      return {
        issuer: {},
        poaps: [],
        awards: [],
        poapsTable: {
          columns: [
            {name: 'id', align: 'left', label: 'ID', field: 'id'},
            {name: 'name', align: 'left', label: 'Name', field: 'name'},
            {
              name: 'image',
              align: 'left',
              label: 'Image',
              field: 'image'
            }
          ],
          pagination: {
            rowsPerPage: 10
          }
        },
        importKeyDialog: {
          show: false,
          data: {
            privateKey: null
          }
        },
        showKeys: false,
        formDialog: {
          show: false,
          useLocation: false,
          data: {}
        },
        urlDialog: {
          show: false,
          data: {}
        }
      }
    },
    computed: {
      geohash() {
        if (this.formDialog.data.lat && this.formDialog.data.long) {
          this.formDialog.data.geohash = gh_encode(
            this.formDialog.data.lat,
            this.formDialog.data.long
          )
          return this.formDialog.data.geohash
        }
      }
    },
    methods: {
      generateKeys: async function () {
        const privateKey = nostr.generatePrivateKey()
        await this.createIssuer(privateKey)
      },
      importKeys: async function () {
        this.importKeyDialog.show = false
        let privateKey = this.importKeyDialog.data.privateKey
        if (!privateKey) {
          return
        }
        try {
          if (privateKey.toLowerCase().startsWith('nsec')) {
            privateKey = nostr.nip19.decode(privateKey).data
          }
        } catch (error) {
          this.$q.notify({
            type: 'negative',
            message: `${error}`
          })
        }
        await this.createIssuer(privateKey)
      },
      showImportKeysDialog: async function () {
        this.importKeyDialog.show = true
      },
      async createIssuer(privateKey) {
        try {
          const pubkey = nostr.getPublicKey(privateKey)
          const payload = {
            private_key: privateKey,
            public_key: pubkey
          }
          const {data} = await LNbits.api.request(
            'POST',
            '/poap/api/v1/issuer',
            this.g.user.wallets[0].adminkey,
            payload
          )
          this.issuer = data
          this.$q.notify({
            type: 'positive',
            message: 'Issuer Created!'
          })
        } catch (error) {
          LNbits.utils.notifyApiError(error)
        }
      },
      async getIssuer() {
        try {
          const {data} = await LNbits.api.request(
            'GET',
            '/poap/api/v1/issuer',
            this.g.user.wallets[0].inkey
          )
          this.issuer = data
          return data
        } catch (error) {
          LNbits.utils.notifyApiError(error)
        }
      },
      toggleIssuerKeys(value) {
        this.showKeys = value
      },
      handleIssuerDeleted() {
        this.issuer = null
        this.showKeys = false
      },
      closeFormDialog() {
        this.formDialog.show = false
        this.formDialog.data = {}
      },
      async getPoaps() {
        try {
          const {data} = await LNbits.api.request(
            'GET',
            '/poap/api/v1/poaps',
            this.g.user.wallets[0].inkey
          )
          this.poaps = [...data].map(mapPoaps)
        } catch (error) {
          LNbits.utils.notifyApiError(error)
        }
      },
      async createPoap() {
        if (this.formDialog.data.id) {
          return this.updatePoap()
        }
        try {
          const formData = this.formDialog.data
          const {data: poap} = await LNbits.api.request(
            'POST',
            '/poap/api/v1/poaps',
            this.g.user.wallets[0].adminkey,
            formData
          )
          this.poaps = [...this.poaps, poap]
          this.closeFormDialog()
        } catch (error) {
          LNbits.utils.notifyApiError(error)
        }
      },
      async updatePoap() {
        try {
          const formData = this.formDialog.data
          
          const {data: poap} = await LNbits.api.request(
            'PUT',
            `/poap/api/v1/poaps/${formData.id}`,
            this.g.user.wallets[0].adminkey,
            formData
          )
          
          this.poaps = this.poaps.map(p => (p.id === poap.id ? poap : p))
          this.closeFormDialog()
        } catch (error) {
          console.error(error)
          LNbits.utils.notifyApiError(error)
        }
      },
      exportCSV: function () {
        LNbits.utils.exportCSV(this.poapsTable.columns, this.poaps)
      },
      openFormDialog(id) {
        const poap = this.poaps.find(p => p.id === id)
        this.formDialog.data = poap
        this.formDialog.show = true
        this.formDialog.useLocation = !!poap.geohash
      },
      openUrlDialog(naddr) {
        // const poap = this.poaps.find(p => p.id === id)
        console.log(naddr)
        this.urlDialog.data = naddr
        this.urlDialog.show = true
      },
      // AWARDS / CLAIMS
      async getAwards() {
        try {
          const {data} = await LNbits.api.request(
            'GET',
            '/poap/api/v1/awards',
            this.g.user.wallets[0].inkey
          )
          this.awards = [...data]
        } catch (error) {
          LNbits.utils.notifyApiError(error)
        }
      }
    },
    async created() {
      await this.getIssuer()
      if (this.issuer.id) {
        await this.getPoaps()
        await this.getAwards()
      }
    }
  })
}

issuer()

// pub: 38f0d5d4504ca0eef6b7435881e499371fb27ca7812cd9bff3e7ee6857a40480
// sec: 8b9c563736267486f467572a297d19012f468c83713fabb70baa6458e45dc0cc

// https://image.nostr.build/ae692f0d98c29e90dbea194608858f078e16d94b2d2bf90e85456e23026bc537.jpg
// https://image.nostr.build/237bf04594f02e4a03d752b4f74adf587998cb5ed23acd7610c73c274acd93c9.jpg
