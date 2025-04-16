from django.shortcuts import render,get_object_or_404
from .models import Antibody,Feedback
from django.http import JsonResponse,HttpResponse
import csv,json
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from .download import download_results
import os, uuid, subprocess
from django.conf import settings

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
            antibodies = Antibody.objects.filter(property_keys__icontains=query)
            print(f"Searching by property: {query}")
        
        result_is_plural=antibodies.count() !=1 and 0
        if not antibodies:
            no_results=True
    else:
        antibodies=Antibody.objects.all()
    results=[]
    
    for antibody in antibodies: 
        results.append({
            'id': antibody.id_db,
            'date':antibody.date,
            'name': antibody.name,
            'reference': antibody.reference,
            'doi': antibody.doi,
            'properties': antibody.property_keys,
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
    sequence = antibody.sequence
    pdb_url = None
    sequence_str = antibody.sequence.get('sequence', '')
    
    # PDB 结构缓存路径
    pdb_filename = f"{id_db}.pdb"
    pdb_path = os.path.join(settings.MEDIA_ROOT, 'pdb', pdb_filename)
    pdb_url = os.path.join(settings.MEDIA_URL, 'pdb', pdb_filename)
    
    if not os.path.exists(pdb_path):
        os.makedirs(os.path.dirname(pdb_path), exist_ok=True)

        # 调用 igfold.py 生成结构文件
        igfold_script = r"D:\VScode\test\IgFold\examples\predict_structure.py"
        command = ["python", igfold_script, "--sequence", sequence_str, "--output", pdb_path]
        print("COMMAND:", command)
        print("TYPES:", [type(arg) for arg in command])
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print("igfold 报错啦：", e)
    return render(request, 'blog/antibody_detail.html',{
        'antibody':antibody,
        'pdb_url': pdb_url,
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
    if antibody.properties:
        if isinstance(antibody.properties, dict):  # 处理 JSON 数据
            for key, value in antibody.properties.items():
                writer.writerow([key, value])
    else:
        writer.writerow(['No properties data available'])

    return response

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