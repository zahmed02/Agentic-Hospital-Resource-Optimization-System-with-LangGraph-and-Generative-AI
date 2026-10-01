'use client'
import { useEffect,useState } from 'react'
import { useParams } from 'next/navigation'
import { getExplanation } from '@/lib/api'
import { InsightView } from '../page'
export default function ExplainabilityDetail(){const params=useParams();const id=params?.id as string;const [data,setData]=useState<any>(null);const [error,setError]=useState('');const load=async()=>{try{setData(await getExplanation(Number(id)))}catch(e:any){setError(e.message)}};useEffect(()=>{if(id)load()},[id]);if(error)return <p className="status-negative">{error}</p>;if(!data)return <p>Loading model insights...</p>;return <InsightView data={data} onRefresh={load}/>}
