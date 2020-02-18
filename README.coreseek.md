# mitmproxy

基于　mitmproxy　，实现对　HTTP/1.1 ，　HTTP2 (gRPC　Included)，　Avro RPC (based on raw TCP)　的拦截分析．

其中，　HTTP/1.1 重点针对　Restful API，即开始　XHR 的请求进行特殊处理．

## 代码理解

- 在　tools/console/windows.py 中，定义了全部使用的 Windows / Panel，称之为　Stack

    > 在　Console 模式下，可以假想为一张张纸片，通过更换纸片的顺序，实现显示不同窗口的内容

- 在　tools/console/defaultkeys.py 中，定义了系统全局的热键绑定

    > 绑定方式为　设定热键，给出要调用的方法，以及生效的上下文

    - B 启动配置好代理服务器的浏览器

- 在　optmanager.py 中，定义了加载配置文件的方式

    eg. 

    ```
    # begin config.yaml 
    console_layout: "horizontal"
    ```
- tools/console/eventlog.py 中，给出了如何显示的简单例子

- 很多功能是作为　addon 提供的，例如保存数据到文件，在　addons/save.py,

    - 默认的情况下，在　界面中　保存的　flow　仅是显示出的
    - 在　addons/view.py 中，处理的数据的选择的范围
    - 在　addons/__init__.py 中，给出了系统默认加载的组件

- 对于　mitmdump ，使用的导出类为 addons/dumper.py

- 每个作为 addon 的模块 , 提供了一个 loader 参数, 类型为 addonmanager . 其中, loader.master 为各自的主程序

    - 对于 mitmdump 为 DumpMaster

- The master handles mitmproxy's main event loop.

- 通过插件增加的参数, 可以通过 --options 参数查看

- 需要修改 options 参数的情况,  通过 --set 指定

    > eg: mitmdump --set flow_detail=3

- 需要进行 flow 的过滤, 代码在 flowfilter.py , 解析 bnf 的过滤器表达.

- 可以通过类似以下命令,进行记录的回放

    > python /home/nzinfo/miniconda3/envs/midproxy/bin/mitmdump -S rec.data --server-replay-nopop --server-replay-refresh

        - rec.data 为记录下的数据
        - server-replay-nopop, 回放之后不移除
        - server-replay-refresh, 自动处理时间更新

- 在回放时, 默认通过 method + URL 进行检索. 但是针对 cookie 状态检测的情况, 应该额外增加 cookie 作为条件
    
    - 可以通过命令行参数 --rheader headername 额外指定需要进行匹配的头部信息
    - 为了能够正确的处理时间, 应记录请求发生时的时间, 便于后续处理增加对应的 time delta 

- 由文件 serverplayback 模块, 处理需要返回的服务器 

    - 实际的加载请求来自 read_flows_from_paths 不是 load_file

    - 通过 _hash 计算 request 的特征值

    - 使用一个数组 key 计算 Hash 值, 最初的构成是 schema method path

        + raw_content 是 HTTP Request 发起时, 附带的数据. 常见在 POST 请求中, GET 请求也可附带
        + server_replay_ignore_content , 仅在 不忽略 content 时使用
            分 multipart_form 和 urlencoded_form 两种情况,
            如果没有在 server_replay_ignore_payload_params 指定, 则 这些 k & v 对中的 k 均 进入 key 数组

            如果 参数没有进入 key, 则  raw_content 作为正文,整体进入
        + server_replay_ignore_host
        + server_replay_ignore_port

        额外的, 增加 host , port 

        + queriesArray 将 query string 解析了, 如果 没有被 server_replay_ignore_params 指定, 则 k & v 分别进入

            * 此处,应该调整为函数调用, 以便于 依据 URL 的上下文, 指定 server_replay_ignore_params

    - key 转为字符传后, 计算 utf8 编码下的 sha256 , utf8 启用 surrogateescape (用于保留无法编码为 utf8 的字符信息)
    - _hash 的实际值, 是在加载后计算的, 同一个 hash 值下, 存在多个 flow ( req&res 对 )
    - mitmproxy 假设服务器端回放的顺序与录制的顺序相同

        * 如果一个 URL 对应多个 response , 回依次返回(全部返回完毕后, 请求源服务器), 如果是 server_replay_nopop 一直返回同一个

- 基于 tag 进行回放控制是不必要的, 完全可以分步执行

    1. 捕获全部 flow
    2. 对捕获到的文件进行过滤, 
        2.1 去掉 asset 文件
        2.2 单独输出 asset 文件

    > mitmdump --anticache -r rec.data -n --set readfile_filter=\!\~a -w 1.data

    从 原始记录中 加载, 过滤掉 asset , 保存到另外一个文件, 类似的相关的 filter 还包括

        - save_stream_filter
        - readfile_filter
        - dumper_filter

## HTTP/1.1

TODO

- [X] 默认不显示 image, css 和　javascript

        - filter 机制默认提供了 ~a 
            ~a      Asset content-type in response. Asset content types are:
                        text/javascript
                        application/x-javascript
                        application/javascript
                        text/css
                        image/*
                        application/x-shockwave-flash
            > "!~a" 过滤条件可用 , 需要注意开启 anticache, 否则返回 304 不能被过滤

            > 对于 bash ,需要自行转意 : mitmdump --anticache --set flow_detail=3 \!\~a  , 用于不显示资源 / asset 文件
        - 具体实现在 flowfilter:FAsset 
        - 额外需要处理的资源
            - application/font-woff2;q=1.0,application/font-woff;q=0.9,*/*;q=0.8

- [ ] 因为服务器　session 状态的不同，同一个　request　可能会存在多个 response.
    
        - 如何推断服务器状态？
            + 技术上,服务器通过 cookie , URL 参数等 判断用户身份.
                * 至少需要一种拦截 cookie 的机制
            + 需要额外的 sesssion 对象，记录　跨越　HTTPFlow　的状态
            + 可以根据某个过滤条件的命中与否，设置对象

        - 提供了 stickycookie 的机制,但是额外引入了过滤器.
            + 只有符合过滤器指定条件的 URL 能够被设置 cookie

- [ ] 能够识别出不同的参数，能够指定（忽略）nonce 参数（　用于防止重放攻击　）
- [ ] 能够指定　nonce　参数的返回规则

## HTTP/2.0

对 gRPC 的支持, 存在现成的工具 https://github.com/bradleyjkemp/grpc-tools . 

通过给 mitmproxy 增加 grpc 支持, 尝试进一步了解 http2 以及 为 avdl2 的支持提供知识积累.


NOTE OF HTTP2 / GRPC

- 在默认情况下, Python 的 gRPC 客户端没有启动加密. 此情况下, 客户端使用 HTTP/2 connections with prior knowledge 的方式发起请求

    > HTTP/2 connections with prior knowledge 尚不被支持.

TODO

- [ ] 未加密的情况下, 支持 HTTP/2 connections with prior knowledge
    需要启用 option ssl_insecure , 设置为不为 0  的值, 默认为 0
    > 实际上, 在 mitmproxy/net/tcp:384 左右, tls.create_client_context 可以给出选项, verify = False
- [ ] ALPN: grpc-exp
    > 目前的分析看, gRPC 默认支持的 APN 为 grpc-exp , h2 . 在 github 上, 出现 grpc-exp 的代码非常少.

    > 实际代码在 mitmproxy/proxy/protocol/tls.py:342 行左右, 调试的输出 options = ['grpc-exp', 'h2'] , 似乎不需要特别处理 

- [ ] 自签名证书

    + 在 mitmproxy/proxy/protocol/http.py:212 行 附近 ,处理 证书相关的问题 

- [ ] gRPC 需要的扩展
    
    Ref: https://github.com/mitmproxy/mitmproxy/issues/3052