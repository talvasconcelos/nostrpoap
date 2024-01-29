async function awardsTable(path) {
  const template = await loadTemplateAsync(path)

  const mapAwards = obj => {
    obj.date = Quasar.utils.date.formatDate(
      new Date(obj.event_created_at * 1000),
      'YYYY-MM-DD HH:mm'
    )
    return obj
  }

  Vue.component('awards-table', {
    name: 'awards-table',
    props: ['awards'],
    template,

    data: function () {
      return {
        selected: [],
        columns: [
          {name: 'id', align: 'left', label: 'ID', field: 'id'},
          {
            name: 'pubkey',
            align: 'left',
            label: 'Pubkey',
            field: 'claim_pubkey',
            format: val => val.slice(0, 6) + '...' + val.slice(-6)
          },
          {
            name: 'bagde',
            align: 'left',
            label: 'POAP ID',
            field: 'badge_id'
          },
          {
            name: 'date',
            align: 'left',
            label: 'Date',
            field: 'date',
            sortable: true
          }
        ]
      }
    },
    computed: {},
    methods: {
      getSelectedString() {
        return this.selected.length === 0
          ? ''
          : `${this.selected.length} record${
              this.selected.length > 1 ? 's' : ''
            } selected of ${this.awards.length}`
      },
      openBulkDialog() {
        alert('Not implemented yet')
      },
      copyText(value) {
        this.$emit('copy-text', value)
      },
      exportCSV: function () {
        const data = this.selected.length === 0 ? this.awards : this.selected
        LNbits.utils.exportCSV(this.columns, data)
      }
    },
    created() {
      this.awards = this.awards.map(mapAwards).sort((a, b) => {
        return b.event_created_at - a.event_created_at
      })
      console.log(this.awards)
    }
  })
}
