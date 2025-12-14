interface PreviewItem {
  personel_id: number
  ad: string
  soyad: string
  brut_maas: number
  unpaid_days?: number
  unpaid_deduction?: number
  sgk_employee?: number
  monthly_income_tax?: number
  overtime_hours?: number
  overtime_pay?: number
  toplam_kesinti?: number
  toplam_ekleme?: number
  net_maas?: number
}

export default function PayrollPreview({ previews, period }: { previews: PreviewItem[]; period: string }) {
  if (!previews || previews.length === 0) return null

  return (
    <div className="card">
      <div className="p-4">
        <h3 className="text-lg font-semibold">Bordro Önizleme - {period}</h3>
        <div className="mt-3 space-y-3">
          {previews.map((p) => {
            const additions: { name: string; amount: number }[] = []
            const deductions: { name: string; amount: number }[] = []

            if (p.overtime_pay && p.overtime_pay > 0) additions.push({ name: 'Ek Mesai', amount: p.overtime_pay })
            if (p.toplam_ekleme && p.toplam_ekleme > 0 && (!p.overtime_pay || p.toplam_ekleme !== p.overtime_pay)) additions.push({ name: 'Diğer Eklemeler', amount: p.toplam_ekleme - (p.overtime_pay || 0) })

            if (p.unpaid_deduction && p.unpaid_deduction > 0) deductions.push({ name: 'Ücretsiz İzin Kesintisi', amount: p.unpaid_deduction })
            if (p.sgk_employee && p.sgk_employee > 0) deductions.push({ name: 'SGK (Çalışan)', amount: p.sgk_employee })
            if (p.monthly_income_tax && p.monthly_income_tax > 0) deductions.push({ name: 'Gelir Vergisi', amount: p.monthly_income_tax })

            return (
              <div key={p.personel_id} className="border rounded-md p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{p.ad} {p.soyad}</div>
                    <div className="text-sm text-slate-500">Brüt: {p.brut_maas.toLocaleString('tr-TR')} ₺</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm">Toplam Kesinti: -{(p.toplam_kesinti || 0).toLocaleString('tr-TR')} ₺</div>
                    <div className="font-semibold text-lg">Net: {(p.net_maas || 0).toLocaleString('tr-TR')} ₺</div>
                  </div>
                </div>

                <div className="mt-3 grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm font-medium mb-2">Eklemeler</div>
                    {additions.length === 0 && <div className="text-sm text-slate-500">— Yok —</div>}
                    {additions.map((a) => (
                      <div key={a.name} className="flex justify-between text-sm">
                        <div className="text-slate-700">{a.name}</div>
                        <div className="text-emerald-600">+{a.amount.toLocaleString('tr-TR')} ₺</div>
                      </div>
                    ))}
                  </div>
                  <div>
                    <div className="text-sm font-medium mb-2">Kesintiler</div>
                    {deductions.length === 0 && <div className="text-sm text-slate-500">— Yok —</div>}
                    {deductions.map((d) => (
                      <div key={d.name} className="flex justify-between text-sm">
                        <div className="text-slate-700">{d.name}</div>
                        <div className="text-red-600">-{d.amount.toLocaleString('tr-TR')} ₺</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
