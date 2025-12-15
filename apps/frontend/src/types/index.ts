export interface User {
  kullanici_id: number
  kullanici_adi: string
  ilk_giris: boolean
  email: string | null
  rol: 'admin' | 'employee'
  personel_id: number | null
}

export interface Employee {
  personel_id: number
  tc_kimlik_no: string
  ad: string
  soyad: string
  dogum_tarihi: string
  telefon: string | null
  email: string | null
  adres: string | null
  ise_giris_tarihi: string
  departman_id: number | null
  departman_adi: string | null
  pozisyon_adi: string | null
  taban_maas: number | null
  aktif_mi: boolean
}

export interface Department {
  id: number
  ad: string
  aciklama: string | null
  personel_sayisi?: number
  departman_id?: number
  departman_adi?: string
}

export interface Position {
  id: number
  ad: string
  departman_id: number | null
  taban_maas: number | null
  pozisyon_id?: number
  pozisyon_adi?: string
  
}

export interface Attendance {
  devam_id: number
  personel_id: number
  tarih: string
  giris_saati: string | null
  cikis_saati: string | null
  durum: 'Normal' | 'Izinli' | 'Devamsiz'
  aciklama: string | null
}

export interface AttendanceRecord {
  personel_id: number
  ad: string
  soyad: string
  tc_kimlik_no: string
  departman_adi: string | null
  bugunku_durum: 'Normal' | 'Izinli' | 'Devamsiz' | null
}

export interface LeaveType {
  id: number
  ad: string
  max_gun: number | null
  aciklama: string | null
  izin_turu_id?: number
  izin_adi?: string
  yillik_hak_gun?: number
  ucretli_mi?: boolean
}

export interface Leave {
  izin_kayit_id: number
  personel_id: number
  izin_turu_id: number
  baslangic_tarihi: string
  bitis_tarihi: string
  gun_sayisi: number
  onay_durumu: 'Beklemede' | 'Onaylandi' | 'Reddedildi'
  ad: string
  soyad: string
  izin_adi: string
}

export interface Salary {
  maas_hesap_id: number
  personel_id: number
  donem_yil: number
  donem_ay: number
  brut_maas: number
  toplam_ekleme: number
  toplam_kesinti: number
  net_maas: number
  odeme_tarihi: string | null
  odendi_mi: boolean
  ad: string
  soyad: string
  departman_adi: string | null
}

export interface DashboardStats {
  toplam: number
  izinli: number
  kalan_calisan: number
  bekleyen: number
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  message?: string
  error?: string
}
