from django.shortcuts import render,get_object_or_404
from .models import Antibody,AntibodyProperty
from django.http import JsonResponse,HttpResponse
import csv,json
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from .download import download_results
import os
from django.conf import settings
from urllib.parse import urljoin
from Bio.Align import PairwiseAligner
import logging
from collections import defaultdict

# Create your views here.
def index(request):
    return render(request, 'blog/index.html')

def antibody_search(request):
    query=request.GET.get('q', '')
    no_results=False
    result_is_plural = False 
    search_type = request.GET.get('type', 'name')
    download = request.GET.get('download', 'false').lower() == 'true'  # 检查是否是下载请求 
    
    if query:
        print(f"Query: {query}")
        print(f"Search type: {search_type}") 
         # 尝试匹配抗体名字
        if search_type == 'name':
            antibodies = Antibody.objects.filter(name__icontains=query)
            print(f"Searching by name: {query}")
            
        else:
        # 匹配抗体性质部分（基于 property_keys 字段）
            antibodies = Antibody.objects.filter(property_list__property_name__icontains=query).distinct()
            print(f"Searching by property: {query}")
            

        
        result_is_plural= len(antibodies) !=1 and 0
        if not antibodies:
            no_results=True
    else:
        antibodies=Antibody.objects.all()
    results=[]
    
    for antibody in antibodies: 
        
        antibody.filtered_properties = [p for p in antibody.property_list.all() if not p.property_name.lower().startswith("assay")]

        results.append({
            'id': antibody.id_db,
            'date':antibody.date,
            'name': antibody.name,
            'paper':antibody.paper,
            'doi': antibody.doi,
            
            'antibody.filtered_properties':antibody.filtered_properties,
        })
    
     # **处理下载请求**
    if download:
        return download_results(query, search_type, antibodies)
    
    page = request.GET.get('page', 1)   # 获取页码，默认为 1
    # 创建分页对象，每页显示 30 个抗体
    paginator = Paginator(antibodies, 30)
    try:
        # 获取当前页的数据
        antibodies_page = paginator.page(page)
    except PageNotAnInteger:
        # 如果页码无效，默认跳转到第一页
        antibodies_page = paginator.page(1)
    except EmptyPage:
        # 如果页码超出范围，返回最后一页
        antibodies_page = paginator.page(paginator.num_pages)


   

    return render(request, 'blog/search_result.html', {
        'antibodies':antibodies, 
        'no_results':no_results,
        'query':query,
        'search_type':search_type,
        'result_is_plural':result_is_plural,
        'antibodies_page':antibodies_page,
        'paginator':paginator,
        'page':page,
        })


def about(request):
    return render(request, 'blog/about.html')

def paper(request):
    return render(request, 'blog/paper.html')

def help(request):
    return render(request, 'blog/help.html')

def contact(request):
    return render(request, 'blog/contact.html')

def antibody_detail(request,id_db):
    antibody=get_object_or_404(Antibody, id_db=id_db)
    sequence= antibody.sequence
    pdb_url = None
    properties = antibody.property_list.all() 
 
    # PDB 结构缓存路径
    pdb_filename = f"{id_db}_tfold_ab.pdb"
    pdb_path = os.path.join(settings.MEDIA_ROOT, 'pdb', pdb_filename)
    pdb_url = urljoin(settings.MEDIA_URL, f'pdb/{pdb_filename}')
    if not os.path.exists(pdb_path):
        os.makedirs(os.path.dirname(pdb_path), exist_ok=True)

    return render(request, 'blog/antibody_detail.html',{
        'antibody':antibody,
        'pdb_url': pdb_url,
        'properties': properties,
    })


def download_all (request, id_db):
    antibody=Antibody.objects.get(id_db=id_db)
    # 创建 HTTP 响应对象，指定文件类型
    response=HttpResponse(content_type='text/csv')
    response['Content-Disposition']=f'attachment;filename="{antibody.id_db}_all_info.csv'
    # 写入 CSV 数据
    writer=csv.writer(response)
    writer.writerow(['Field','Value'])
    # 写入抗体的基本信息
    writer.writerow(['ID',antibody.id_db])
    writer.writerow(['Name',antibody.name])
    writer.writerow(['Name',antibody.format])
    writer.writerow(['Name',antibody.other_id])
    writer.writerow(['Name',antibody.organism])
    writer.writerow(['Name',antibody.paper])
    writer.writerow(['Reference', antibody.reference])
    writer.writerow(['DOI', antibody.doi])
    writer.writerow(['Sequence', ''])
    if antibody.sequence:
        if isinstance(antibody.sequence, dict):  # 处理 JSON 数据
            for region, seq in antibody.sequence.items():
                writer.writerow([region, seq])
    else:
        writer.writerow("No sequence data available.")
    writer.writerow(['Properties', ''])
    property_list = antibody.property_list.all()
    if property_list.exists():
        writer.writerow(['Property Name', 'Value', 'Assay'])
        for prop in property_list:
            writer.writerow([prop.property_name, prop.value, prop.assay or ''])
    else:
        writer.writerow(['No properties data available'])

def download_sequence(request, id_db):
    antibody = Antibody.objects.get(id_db=id_db)
    
    # 创建 HTTP 响应对象，指定文件类型
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{antibody.id_db}_sequence.fasta"'

    # 写入抗体序列
    response.write(f"Antibody ID: {antibody.id_db}\n")
    response.write(f"Name: {antibody.name}\n")
    response.write(f"\nSequence:\n")
    if antibody.sequence:
        if isinstance(antibody.sequence, dict):  # 处理 JSON 数据
            for region, seq in antibody.sequence.items():
                response.write(f"\n{region} sequence:\n{seq}\n")
    else:
        response.write("No sequence data available.\n")

    return response

def check_pdb(request, id_db):
    path = os.path.join(settings.MEDIA_ROOT, 'pdb', f'{id_db}.pdb')
    if os.path.exists(path):
        return HttpResponse(f"PDB file for {id_db} exists.")
    else:
        return HttpResponse(f"PDB file for {id_db} NOT found.")
    


logger = logging.getLogger(__name__)

# 指定用于比对的区域字段
VARIABLE_REGIONS = [
    "sequence_VH", "sequence_VL",
    "sequence_Fv", "sequence-Fab", "sequence_FabH", "sequence_FabL"
]

def compare_sequences(query_seq, db_seq):
    if not query_seq or not db_seq:
        return {'score': 0.0, 'identity': 0.0, 'coverage': 0.0, }
    aligner = PairwiseAligner()
    aligner.mode = 'global'
    alignment = aligner.align(query_seq, db_seq)[0]

    aligned_query = alignment.aligned[0]
    matches = sum(e2 - e1 for (e1, e2) in aligned_query)
    total_length = max(len(query_seq), len(db_seq))

    identity = matches / total_length * 100
    coverage = matches / len(query_seq) * 100
    score = alignment.score / total_length

    return {
        'score': round(score, 3),
        'identity': round(identity, 2),
        'coverage': round(coverage, 2)
    }

def sequence_similarity(request):
    if request.method == "POST":
        try:
            user_seq = request.POST.get("sequence", "").strip().upper()
            region = request.POST.get("region", "").strip()

            if not user_seq or not region:
                return render(request, "blog/sequence_search.html", {
                    "error": "Please enter sequence and select region.",
                    "query": user_seq,
                    "region": region,
                    "has_searched": True,
                })

            results = []
            for ab in Antibody.objects.all():
                seq_dict = ab.sequence or {}
                db_seq = seq_dict.get(region)
                if db_seq:
                    db_seq = db_seq.upper()
                    metrics = compare_sequences(user_seq, db_seq)
                    if metrics["score"] > 0.5:
                        results.append({
                            "id_db": ab.id_db,
                            "antibody": ab.name,
                            "region": region,
                            "score": round(metrics["score"] * 100, 2),
                            "identity": round(metrics["identity"], 2),
                            "coverage": round(metrics["coverage"], 2),
                        })

            results.sort(key=lambda x: x["score"], reverse=True)

            if not results:
                return render(request, "blog/sequence_search.html", {
                    "error": "No antibody found.",
                    "query": user_seq,
                    "region": region,
                    "has_searched": True,
                })

            return render(request, "blog/sequence_search.html", {
                "results": results,
                "query": user_seq,
                "region": region,
                "has_searched": True,
            })

        except Exception:
            return render(request, "blog/sequence_search.html", {
                "error": "An internal error occurred. Please try again later.",
                "has_searched": True,
            })

    # GET 请求：没有查询过
    return render(request, "blog/sequence_search.html", {"has_searched": False})
