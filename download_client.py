import requests
import getpass
import sys
import time

def download_image():
    print("=== Harbor 镜像下载客户端 ===")
    
    # 默认配置
    default_harbor = "https://10.3.2.40"
    default_image = "bj-tgy/dev/tgy-ui-amd64"
    default_tag = "latest"
    api_url = "http://localhost:5001/api/docker/download"

    # 获取输入
    harbor_url = input(f"Harbor URL [{default_harbor}]: ").strip() or default_harbor
    username = input("用户名: ").strip()
    if not username:
        print("错误: 用户名不能为空")
        return
    
    password = getpass.getpass("密码: ").strip()
    if not password:
        print("错误: 密码不能为空")
        return

    image = input(f"镜像名称 (项目/仓库) [{default_image}]: ").strip() or default_image
    tag = input(f"标签 [{default_tag}]: ").strip() or default_tag

    # 构造请求数据
    payload = {
        "harborUrl": harbor_url,
        "username": username,
        "password": password,
        "image": image,
        "tag": tag
    }

    print(f"\n正在请求下载 {image}:{tag} ...")
    print("这可能需要几分钟，取决于镜像大小...")

    try:
        start_time = time.time()
        # 发送请求，stream=True 用于流式下载
        response = requests.post(api_url, json=payload, stream=True)
        
        if response.status_code == 200:
            # 从响应头获取文件名（如果有）
            # Content-Disposition: attachment; filename=...
            filename = f"{image.replace('/', '_')}_{tag}.tar.gz"
            
            total_size = 0
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)
                        # 简单的进度显示
                        sys.stdout.write(f"\r已下载: {total_size / 1024 / 1024:.2f} MB")
                        sys.stdout.flush()
            
            duration = time.time() - start_time
            print(f"\n\n✅ 下载成功!")
            print(f"文件保存为: {filename}")
            print(f"总大小: {total_size / 1024 / 1024:.2f} MB")
            print(f"耗时: {duration:.1f} 秒")
        else:
            print(f"\n❌ 下载失败 (状态码 {response.status_code})")
            try:
                error_data = response.json()
                print(f"错误信息: {error_data.get('message', '未知错误')}")
                if 'details' in error_data:
                    print(f"详情: {error_data['details']}")
            except:
                print(f"响应内容: {response.text[:200]}")

    except requests.exceptions.ConnectionError:
        print(f"\n❌ 无法连接到后端服务 ({api_url})")
        print("请确保 python app.py 正在运行")
    except Exception as e:
        print(f"\n❌ 发生异常: {str(e)}")

if __name__ == "__main__":
    download_image()
